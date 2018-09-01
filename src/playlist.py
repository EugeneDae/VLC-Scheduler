import os, re, logging, datetime, random, itertools

import utils


class Playlist:
    _sources = []
    _items = []
    
    def __init__(self, config):
        self.config = config
        
        if config.SOURCE_MIXING_FUNCTION == 'chain':
            from itertools import chain as source_mixing_function
        else:
            from utils import zip_equally as source_mixing_function
        
        self.source_mixing_function = source_mixing_function
    
    @property
    def allowed_extensions(self):
        return ['.' + i.lower() for i in self.config.ALLOWED_EXTENSIONS]
    
    @property
    def filename_with_a_date_regex(self):
        return re.compile(self.config.FILENAME_WITH_A_DATE_REGEX)
    
    def prepare_source(self, source):
        result = {}
        result['active'] = True
        result['path'] = source['path']
        result['shuffle'] = bool(source.get('shuffle', False))
        result['item_play_duration'] = int(source.get('item_play_duration', 60))
        result['playing_time'] = source.get('playing_time', [])
        
        if result['playing_time']:
            start_time, end_time = (
                datetime.datetime.strptime(i, '%H:%M').time() for i
                in utils.parse_time_interval(result['playing_time'])
            )
            
            result['playing_time'] = start_time, end_time
            
            now_time = datetime.datetime.now().time()
            
            if not utils.is_time_within_interval(now_time, start_time, end_time):
                result['active'] = False
        
        return result
    
    def get_sources(self):
        if not self._sources:
            for source in self.config.SOURCES:
                self._sources.append(self.prepare_source(source))
        
        return self._sources
    
    def get_active_sources(self):
        for source in self.get_sources():
            if source['active']:
                yield source
            else:
                logging.warning('Skipped source: %s (reason: playing_time).' % source['path'])
    
    def get_rebuild_schedule(self):
        schedule = ['00:00']
        
        for source in self.get_sources():
            for time in source['playing_time']:
                time_str = time.strftime('%H:%M')  # this is really stupid
                
                if time_str not in schedule:
                    schedule.append(time_str)
        
        return sorted(schedule)
    
    def get_source_contents(self, source):
        paths = list(utils.list_files_with_extensions(
            source['path'], self.allowed_extensions
        ))
        
        if source['shuffle']:
            random.shuffle(paths)
        else:
            paths = sorted(paths)
        
        for path in paths:
            match = self.filename_with_a_date_regex.match(os.path.basename(path))
            
            if match:
                date = datetime.date(
                    year=int(match[3]),
                    month=int(match[2]),
                    day=int(match[1])
                )
                
                if date != datetime.date.today():
                    logging.warning(
                        'Skipped file: %s ' % path +
                        '(reason: filename contains a date that is not today).'
                    )
                    continue
            
            yield {'path': path, 'item_play_duration': source['item_play_duration']}
    
    def rebuild(self, ignore_playing_time=False):
        self._sources = []
        self._items = []
        
        if ignore_playing_time:
            active_sources = list(self.get_sources())
        else:
            active_sources = list(self.get_active_sources())
        
        contents = [list(self.get_source_contents(s)) for s in active_sources]
        
        for item in self.source_mixing_function(*contents):
            self._items.append(item)
        
        self._items_cycle = itertools.cycle(self._items)
        
        if len(self._items) > 0:
            logging.info(
                'The playlist has been rebuilt from %i source(s) and %i file(s).' %
                (len(active_sources), len([i for c in contents for i in c])) +
                '\n\t' + '\n\t'.join([i['path'] for i in self._items])
            )
        else:
            if not ignore_playing_time and self.config.IGNORE_PLAYING_TIME_IF_PLAYLIST_IS_EMPTY:
                logging.warning(
                    'The playlist appears to be empty, but '
                    'IGNORE_PLAYING_TIME_IF_PLAYLIST_IS_EMPTY is set. '
                    'Rebuilding again.'
                )
                
                return self.rebuild(ignore_playing_time=True)
            else:
                logging.warning('The playlist appears to be empty.')
    
    def get_items(self):
        return self._items
    
    def get_next_in_cycle(self):
        return next(self._items_cycle)
