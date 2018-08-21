import os, re, datetime
from random import shuffle

from config import config, logger
from utils import list_files_with_extensions, parse_time_interval

if config.MIXING_FUNCTION == 'chain':
    from itertools import chain as mixing_function
else:
    from utils import zip_equally as mixing_function


ALLOWED_EXTENSIONS = ['.' + i.lower() for i in config.ALLOWED_EXTENSIONS]
FILENAME_WITH_A_DATE_REGEX = re.compile(config.FILENAME_WITH_A_DATE_REGEX)


def build_playlist():
    def list_files(source):
        paths = list(list_files_with_extensions(
            source['path'], ALLOWED_EXTENSIONS
        ))
        
        if source.get('shuffle') and source['shuffle']:
            shuffle(paths)
        else:
            paths = sorted(paths)
        
        for path in paths:
            match = FILENAME_WITH_A_DATE_REGEX.match(os.path.basename(path))
            
            if match:
                date = datetime.date(
                    year=int(match[3]),
                    month=int(match[2]),
                    day=int(match[1])
                )
                
                if date != datetime.date.today():
                    logger.info(
                        'Skipped file: %s ' % path +
                        '(reason: filename contains a date that is not today).'
                    )
                    continue
            
            yield {'path': path, 'repeat_each_file': source['repeat_each_file']}
    
    def list_sources():
        for source in config.SOURCES:
            # Check if repeat_each_file is int
            source['repeat_each_file'] = int(source.get('repeat_each_file', 1))
            
            # Check if the source is meant to be played at this hour
            playing_time = source.get('playing_time')
            if playing_time:
                time_now = datetime.datetime.now().time()
                
                time_start, time_end = [
                    datetime.datetime.strptime(i, '%H:%M').time() for i in
                    parse_time_interval(playing_time)
                ]
                
                if not (time_now >= time_start and time_now < time_end):
                    logger.info(
                        'Skipped source: %s ' % source['path'] +
                        '(reason: playing_time).'
                    )
                    continue
            
            logger.info('Added source: %s.' % source['path'])
            yield list_files(source)
    
    stat = []
    for item in mixing_function(*[list(i) for i in list_sources()]):
        if item['repeat_each_file'] > 1:
            logger.info('Added file: %s (will repeat %i times).' % (
                item['path'], item['repeat_each_file']
            ))
        else:
            logger.info('Added file: %s.' % item['path'])
        
        stat.append(item['path'])
        
        for _ in range(item['repeat_each_file']):
            yield item['path']
    logger.info('In total %i file(s) added.' % len(list(set(stat))))
