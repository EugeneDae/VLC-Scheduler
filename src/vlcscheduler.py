import os, sys, asyncio, traceback
from threading import Timer

import click, schedule
from watchgod import awatch

from config import config, logger
from watchers import VLCSchedulerSourceWatcher
from playlist import Playlist
import vlc

VERSION = '0.2.0-alpha'


def check_config():
    if len(config.SOURCES) == 0:
        return sys.exit('Please define at least one source in the configuration file.')
    
    for source in config.SOURCES:
        if not os.path.isdir(source['path']):
            return sys.exit('The source path is not a directory: %s.' % source['path'])
    
    if not os.path.isfile(config.VLC['path']):
        return sys.exit('Invalid path to VLC: %s.' % config.VLC['path'])


def playlist_event_handler(event):
    global PLAYER
    
    playlist = event.source
    
    if len(playlist.get_items()) == 0:
        PLAYER.empty()


async def watchgod_coro(path, action):
    global PLAYER
    global REBUILD_TIMER
    REBUILD_TIMER = None
    
    async for changes in awatch(path, watcher_cls=VLCSchedulerSourceWatcher):
        logger.info('%s changed, the playlist will be rebuilt in %i seconds.' % (
            path, config.REBUILD_DELAY
        ))
        
        try:
            REBUILD_TIMER.cancel()
        except (AttributeError, NameError):
            pass
        
        REBUILD_TIMER = Timer(config.REBUILD_DELAY, action)
        REBUILD_TIMER.start()
        
        # Prevent VLC from hanging
        if not os.path.isfile(PLAYER.current_item['path']):
            PLAYER.empty()


async def schedule_coro():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def player_coro(playlist):
    global PLAYER
    
    while True:
        try:
            item = playlist.get_next_in_cycle()
        except StopIteration:
            await asyncio.sleep(1)
        else:
            if not os.path.isfile(item['path']):
                logging.info('%s does not exist anymore, skipping.' % item['path'])
                continue
            
            logger.info('Now playing %(path)s for %(item_play_duration)i seconds.' % item)
            PLAYER.add(item['path'])
            PLAYER.current_item = item
            await asyncio.sleep(item['item_play_duration'])


async def test_coro(playlist):
    pass
    # await playlist.wait_for_rebuild()
    # print('!!!!!!!!!!!!!!!!!!!!!!!!!')


async def main_coro():
    global PLAYER
    
    check_config()
    
    # Setup VLC
    launcher = vlc.VLCLauncher(config.VLC, debug=config.DEBUG)
    await launcher.launch()
    PLAYER = vlc.VLCHTTPClient(config.VLC)
    PLAYER.current_item = {'path': None}  # dirty, but works
    
    # Setup the playlist
    playlist = Playlist(config)
    playlist.subscribe(playlist_event_handler)
    playlist.rebuild()
    
    # Setup the rebuild schedule
    rebuild_schedule = playlist.get_rebuild_schedule()
    for time in rebuild_schedule:
        schedule.every().day.at(time).do(playlist.rebuild)
    logger.info('Rebuilds will run at: %s.' % ', '.join(rebuild_schedule))
    
    # Setup coroutines
    tasks = [
        launcher.watch_exit(), schedule_coro(),
        player_coro(playlist), test_coro(playlist)
    ]
    
    for source in config.SOURCES:
        tasks.append(watchgod_coro(source['path'], action=playlist.rebuild))
    
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
    global REBUILD_TIMER
    
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
        
        try:
            REBUILD_TIMER.cancel()
        except (AttributeError, NameError):
            pass


if __name__ == '__main__':
    main()
