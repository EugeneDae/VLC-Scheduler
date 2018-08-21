import os, sys, asyncio
from threading import Timer

import click, schedule
from watchgod import awatch

from config import config, logger
from watchers import VLCSchedulerSourceWatcher
from utils import parse_time_interval
from playlist import build_playlist
from vlc import VLCLauncher, VLCHTTPClient

VERSION = '0.1.0-alpha'
REBUILD_TIMER = None
REBUILD_SCHEDULE = ['00:00']


def rebuild():
    if config.VLC['launch'] and config.VLC['path']:
        launcher = VLCLauncher(config.VLC)
        launcher.launch()
    
    player = VLCHTTPClient(config.VLC)
    
    player.empty()
    
    for item in build_playlist():
        player.enqueue(item)
    
    player.play()
    
    logger.info('Rebuild complete. Sleeping...')


def check_config():
    if len(config.SOURCES) == 0:
        return sys.exit('Please define at least one source in the configuration file.')
    
    for source in config.SOURCES:
        if not os.path.isdir(source['path']):
            return sys.exit('The source path is not a directory: %s.' % source['path'])
    
    if not os.path.isfile(config.VLC['path']):
        return sys.exit('Invalid path to VLC: %s.' % config.VLC['path'])


def prepare_schedule():
    global REBUILD_SCHEDULE
    
    for source in config.SOURCES:
        if source.get('playing_time'):
            times = parse_time_interval(source['playing_time'])
            for t in times:
                if t not in REBUILD_SCHEDULE:
                    REBUILD_SCHEDULE.append(t)
            REBUILD_SCHEDULE = sorted(REBUILD_SCHEDULE)
    
    for t in REBUILD_SCHEDULE:
        schedule.every().day.at(t).do(rebuild)
    
    logger.info('Rebuilds will run at: %s.' % ', '.join(REBUILD_SCHEDULE))


async def watchgod_coro(path):
    global REBUILD_TIMER
    
    async for changes in awatch(path, watcher_cls=VLCSchedulerSourceWatcher):
        logger.info('%s changed, rebuild will run in %i seconds.' % (
            path, config.REBUILD_DELAY
        ))
        
        try:
            REBUILD_TIMER.cancel()
        except AttributeError:
            pass
        
        REBUILD_TIMER = Timer(config.REBUILD_DELAY, rebuild)
        REBUILD_TIMER.start()


async def schedule_coro():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main_coro():
    tasks = []
    tasks.append(schedule_coro())
    
    for source in config.SOURCES:
        tasks.append(watchgod_coro(source['path']))
    
    await asyncio.gather(*tasks)


@click.command()
@click.version_option(VERSION)
def main():
    check_config()
    
    logger.info('VLC Scheduler v%s started.' % VERSION)
    
    prepare_schedule()
    
    rebuild()
    
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(main_coro())
    finally:
        logger.info('VLC Scheduler stopped.')
        
        try:
            REBUILD_TIMER.cancel()
        except AttributeError:
            pass
        
        loop.close()


if __name__ == '__main__':
    main()
