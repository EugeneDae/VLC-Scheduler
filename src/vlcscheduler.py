import os, sys, asyncio, traceback

import click, schedule
from watchgod import awatch

from config import config, logger
from watchers import VLCSchedulerSourceWatcher
from playlist import Playlist
import version, vlc


async def watchgod_coro(path, action):
    async for changes in awatch(path, watcher_cls=VLCSchedulerSourceWatcher, debounce=3600):
        logger.info('Changes detected in %s.' % path)
        action()


async def schedule_coro():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def player_coro(player, rebuild_events_queue, extra_items_queue):
    playlist = None
    
    while True:
        if not playlist:
            current_item_path = None
            player.empty()
            playlist = await rebuild_events_queue.get()
        
        try:
            try:
                item = extra_items_queue.get_nowait()
            except asyncio.QueueEmpty:
                item = playlist.get_next()
        except StopIteration:
            # The playlist is empty, so throw it away
            playlist = None
            continue
        else:
            # VLC hangs horribly when asked to open a non-existing file
            if not os.path.isfile(item.path):
                logger.warning((
                    '%s does not exist anymore, but normally this shouldn’t happen. '
                    'Stopping until next rebuild.'
                ) % item.path)
                playlist = None
                continue
            
            play_duration = item.source.item_play_duration
            
            if item.path != current_item_path:
                # VLC occasionally chokes on playlists and keeps playing what it was playing
                if item.path.lower().endswith(config.PLAYLIST_EXTENSIONS):
                    player.empty()
                
                player.add(item.path)
            
            if play_duration == 0:
                await asyncio.sleep(0.25)
                play_duration = player.status().get('length', 0)
                
                if play_duration <= 0:
                    play_duration = config.IMAGE_PLAY_DURATION
            
            if item.path != current_item_path:
                logger.info('Playing %s for %i seconds.' % (item.path, play_duration))
                current_item_path = item.path
            
            finished, pending = await asyncio.wait(
                [asyncio.sleep(play_duration), rebuild_events_queue.get()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in finished:
                result = task.result()
                
                if result:  # we have a new playlist
                    playlist = result
                    current_item_path = None
                    player.empty()
            
            for task in pending:
                task.cancel()


async def main_coro():
    # Setup VLC
    launcher = vlc.VLCLauncher(config.VLC, debug=config.DEBUG)
    await launcher.launch()
    player = vlc.VLCHTTPClient(config.VLC)
    
    # Setup playlists
    default_playlist_config = {
        'allowed_extensions': tuple(list(config.MEDIA_EXTENSIONS) + list(config.PLAYLIST_EXTENSIONS)),
        'filename_with_a_date_pattern': config.FILENAME_WITH_A_DATE_PATTERN
    }

    primary_playlist = Playlist(
        name='PRIMARY', **default_playlist_config, recursive=config.MEDIA_RECURSIVE,
        ignore_playing_time_if_empty=config.IGNORE_PLAYING_TIME_IF_PLAYLIST_IS_EMPTY
    )
    special_playlist = Playlist(
        name='SPECIAL', **default_playlist_config, recursive=config.MEDIA_RECURSIVE
    )
    adverts_playlist = Playlist(
        name='ADS', **default_playlist_config, recursive=config.MEDIA_RECURSIVE,
        source_mixing_function='chain'
    )
    
    for source in config.SOURCES:
        if source.get('play_every_minutes'):
            adverts_playlist.add_source(source)
        elif source.get('special'):
            special_playlist.add_source(source)
        else:
            primary_playlist.add_source(source)
    
    # Queues
    rebuild_events_queue = asyncio.Queue()
    periodic_items_queue = asyncio.Queue()
    
    # Rebuild
    def rebuild():
        rebuild_events_queue.empty()
        periodic_items_queue.empty()
        schedule.clear('ads')
        
        primary_playlist.build()
        special_playlist.build()
        
        # Choose current playlist
        if special_playlist.is_empty():
            selected_playlist = primary_playlist
            adverts_playlist.build()
            
            if primary_playlist.is_empty():
                # Only run ads if there's other content
                if not adverts_playlist.is_empty():
                    logger.warning('Ads will run only when there is other content.')
            else:
                for item in adverts_playlist.get_items():
                    logger.info((
                        'Scheduling {0.path} to run every {0.source.play_every_minutes} minute(s).'
                    ).format(item))
                    
                    def enqueue(item=item):
                        return periodic_items_queue.put_nowait(item)
                    
                    schedule.every(item.source.play_every_minutes).minutes.do(enqueue).tag('ads')
        else:
            logger.info('Playing %s playlist instead of everything else.' % special_playlist.name)
            selected_playlist = special_playlist
        
        rebuild_events_queue.put_nowait(selected_playlist)
    
    rebuild()
    
    # Setup the rebuild schedule
    rebuild_schedule = ['00:00']
    for playlist in (primary_playlist, special_playlist, adverts_playlist):
        times = playlist.get_rebuild_schedule()
        for time in times:
            time_str = time.strftime('%H:%M')  # schedule doesn't support time objects
            if time_str not in rebuild_schedule:
                rebuild_schedule.append(time_str)
    
    for time_str in rebuild_schedule:
        schedule.every().day.at(time_str).do(rebuild)
    
    logger.info('Rebuilds will run at: %s.' % ', '.join(sorted(rebuild_schedule)))
    
    # Setup coroutines
    tasks = [
        launcher.watch_exit(), schedule_coro(),
        player_coro(player, rebuild_events_queue, periodic_items_queue)
    ]
    
    for source in config.SOURCES:
        tasks.append(watchgod_coro(source['path'], action=rebuild))
    
    await asyncio.gather(*tasks)


@click.command()
@click.version_option(version.VERSION)
def main():
    logger.info('VLC Scheduler v%s started.' % version.VERSION)
    
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(main_coro())
    except Exception as e:
        if config.DEBUG:
            logger.fatal(traceback.format_exc())
        else:
            logger.fatal(str(e))
    finally:
        loop.close()
        logger.info('VLC Scheduler stopped.')


if __name__ == '__main__':
    main()
