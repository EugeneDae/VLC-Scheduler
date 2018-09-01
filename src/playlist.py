import os, re, logging, datetime, random, itertools

import utils


class Playlist:
    _sources = []
    _items = []
    
    class Event:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def __init__(self, config):
        self.config = config
        self.callbacks = set()
        
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
                logging.info('Skipped source: %s (reason: playing_time).' % result['path'])
        
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
                    logging.info(
                        'Skipped file: %s ' % path +
                        '(reason: filename contains a date that is not today).'
                    )
                    continue
            
            yield {'path': path, 'item_play_duration': source['item_play_duration']}
    
    def rebuild(self):
        self._sources = []
        self._items = []
        contents = [list(self.get_source_contents(s)) for s in self.get_active_sources()]
        
        for item in self.source_mixing_function(*contents):
            self._items.append(item)
        
        self._items_cycle = itertools.cycle(self._items)
        
        if len(self._items) > 0:        
            logging.info(
                'The playlist has been rebuilt from %i file(s).' % 
                len([i for c in contents for i in c]) +
                '\n\t' + '\n\t'.join([i['path'] for i in self._items])
            )
        else:
            logging.info('The playlist appears to be empty.')
        
        self.fire(type='rebuild')
    
    def get_items(self):
        return self._items
    
    def get_next_in_cycle(self):
        return next(self._items_cycle)
    
    def subscribe(self, callback):
        self.callbacks.add(callback)
    
    def unsubscribe(self, callback):
        self.callbacks.discard(callback)
    
    def fire(self, **attrs):
        e = self.Event(source=self, **attrs)
        
        for fn in self.callbacks:
            fn(e)
