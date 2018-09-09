import os, sys, asyncio, traceback

import click, schedule
from watchgod import awatch

from config import config, logger
from watchers import VLCSchedulerSourceWatcher
from playlist import Playlist
import vlc

VERSION = '0.2.1-alpha'


def check_config():
    if len(config.SOURCES) == 0:
        return sys.exit('Please define at least one source in the configuration file.')
    
    for source in config.SOURCES:
        if not os.path.isdir(source['path']):
            return sys.exit('The source path is not a directory: %s.' % source['path'])
    
    if not os.path.isfile(config.VLC['path']):
        return sys.exit('Invalid path to VLC: %s.' % config.VLC['path'])


async def watchgod_coro(path, action):
    async for changes in awatch(path, watcher_cls=VLCSchedulerSourceWatcher, debounce=3600):
        action()


async def schedule_coro():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def player_coro(player, playlist, post_rebuild_events):
    current_item_path = None
    
    file_error_count = 0
    file_error_threshold = 2
    
    player.empty()
    
    while True:
        # Too many errors => wait for the next rebuild
        if file_error_count > file_error_threshold:
            logger.warning('Too many files in the playlist do not exist anymore.')
            file_error_count = 0
            player.empty()
            current_item_path = None
            await post_rebuild_events.get()
        
        try:
            item = playlist.get_next_in_cycle()
        except StopIteration:
            # If the playlist is empty, empty the VLC playlist and
            # wait for the next rebuild
            player.empty()
            current_item_path = None
            await post_rebuild_events.get()
        else:
            # If the file doesn't exist anymore, don't feed it to VLC
            if not os.path.isfile(item.path):
                logger.warning('%s does not exist anymore, skipping.' % item.path)
                file_error_count += 1
                continue
            
            play_duration = item.source.item_play_duration
            
            if item.path != current_item_path:
                player.add(item.path)
                
                if play_duration == 0:
                    await asyncio.sleep(0.25)
                    length = player.status().get('length', 0)
                    
                    if length <= 0:
                        length = config.IMAGE_PLAY_DURATION
                    
                    play_duration = length
                
                logger.info('Now playing %s for %i seconds.' % (item.path, play_duration))
            
            current_item_path = item.path
            
            _, pending = await asyncio.wait(
                [asyncio.sleep(play_duration), post_rebuild_events.get()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()


async def main_coro():
    check_config()
    
    # Setup VLC
    launcher = vlc.VLCLauncher(config.VLC, debug=config.DEBUG)
    await launcher.launch()
    player = vlc.VLCHTTPClient(config.VLC)
    
    # Setup the playlist
    playlist = Playlist(config)
    post_rebuild_events = asyncio.Queue()
    
    # Rebuild
    def rebuild(emit_event=True):
        res = playlist.rebuild()
        
        if emit_event:
            post_rebuild_events.put_nowait(res)
        
    
    rebuild(False)
    
    # Setup the rebuild schedule
    rebuild_schedule = playlist.get_rebuild_schedule()
    for time in rebuild_schedule:
        schedule.every().day.at(time).do(rebuild)
    logger.info('Rebuilds will run at: %s.' % ', '.join(rebuild_schedule))
    
    # Setup coroutines
    tasks = [
        launcher.watch_exit(), schedule_coro(),
        player_coro(player, playlist, post_rebuild_events)
    ]
    
    for source in config.SOURCES:
        tasks.append(watchgod_coro(source['path'], action=rebuild))
    
    try:
        await asyncio.gather(*tasks)
    except vlc.VLCError as e:
        if config.DEBUG:
            logger.fatal(traceback.format_exc())
        else:
            logger.fatal(str(e))


@click.command()
@click.version_option(VERSION)
def main():
    logger.info('VLC Scheduler v%s started.' % VERSION)
    
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(main_coro())
    finally:
        loop.close()
        logger.info('VLC Scheduler stopped.')


if __name__ == '__main__':
    main()
