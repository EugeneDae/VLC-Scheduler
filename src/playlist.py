import os, re, logging, datetime, random, itertools, types

import utils


class Playlist:
    def __init__(self, sources=[], name='Untitled', allowed_extensions=[],
                 source_mixing_function='zip_equally', recursive=False, 
                 filename_with_a_date_pattern='^(\d\d)-(\d\d)-(\d\d\d\d).*',
                 ignore_playing_time_if_empty=False):
        
        self._sources = []
        
        # Process kwargs
        self.add_source(*sources)
        self.name = name
        self._allowed_extensions = allowed_extensions
        self._filename_with_a_date_regex = re.compile(filename_with_a_date_pattern)
        self._ignore_playing_time_if_empty = ignore_playing_time_if_empty
        self._recursive = recursive
        
        # self._source_mixing_function
        if source_mixing_function == 'zip_equally':
            self._source_mixing_function = utils.zip_equally
        elif source_mixing_function == 'chain':
            self._source_mixing_function = itertools.chain
        else:
            raise ValueError('Unsupported <source_mixing_function>')
    
    def prepare_source(self, source):
        prepared = types.SimpleNamespace(
            active=True,
            path=source['path'],
            shuffle=bool(source.get('shuffle', False)),
            recursive=bool(source.get('recursive', self._recursive)),
            item_play_duration=int(source.get('item_play_duration', 0)),
            play_every_minutes=int(source.get('play_every_minutes', 0)),
            start_time=None,
            end_time=None
        )
        
        if source.get('playing_time'):
            prepared.start_time, prepared.end_time = (
                datetime.datetime.strptime(i, '%H:%M').time() for i
                in utils.parse_time_interval(source['playing_time'])
            )
        
        return prepared
    
    def add_source(self, *sources):
        for source in sources:
            self._sources.append(self.prepare_source(source))
    
    def get_sources(self):
        return self._sources
    
    def get_active_sources(self):
        for source in self.get_sources():
            if source.active:
                yield source
    
    def check_sources(self):
        now_time = datetime.datetime.now().time()
        
        for source in self.get_sources():
            source.active = True
            
            if source.start_time and source.end_time:
                if not utils.is_time_within_interval(now_time, source.start_time, source.end_time):
                    source.active = False
    
    def get_rebuild_schedule(self):
        rebuild_schedule = []
        
        for source in self.get_sources():
            for time in (source.start_time, source.end_time):                
                if time and time not in rebuild_schedule:
                    rebuild_schedule.append(time)
        
        return sorted(rebuild_schedule)
    
    def get_source_contents(self, source):
        paths = list(utils.list_files_with_extensions(
            source.path, self._allowed_extensions, recursive=source.recursive
        ))
        
        if source.shuffle:
            random.shuffle(paths)
        else:
            paths = sorted(paths)
        
        for path in paths:
            match = self._filename_with_a_date_regex.match(os.path.basename(path))
            
            if match:
                date = datetime.date(
                    year=int(match[3]),
                    month=int(match[2]),
                    day=int(match[1])
                )
                
                if date != datetime.date.today():
                    logging.warning(
                        'Skipping: %s (reason: filename date ≠ today).' % path
                    )
                    continue
            
            yield types.SimpleNamespace(path=path, source=source)
    
    def build(self, use_only_active_sources=True):
        self._items = []
        
        self.check_sources()
        
        if use_only_active_sources:
            sources = list(self.get_active_sources())
        else:
            sources = list(self.get_sources())
        
        contents = [list(self.get_source_contents(s)) for s in sources]
        
        for item in self._source_mixing_function(*contents):
            self._items.append(item)
        
        self._items_cycle = itertools.cycle(self._items)
        
        if self.is_empty():
            if use_only_active_sources and self._ignore_playing_time_if_empty:
                logging.warning((
                    'Building playlist %s while ignoring '
                    '<playing_time> of the sources.'
                ) % self.name)
                return self.build(use_only_active_sources=False)
            else:
                logging.warning('Playlist %s is empty.' % self.name)
        else:
            num_s = len(sources)
            num_f = len([i for c in contents for i in c])
            
            logging.info(
                'Playlist %s has been built from %i source(s) and %i file(s).' % (
                    self.name, num_s, num_f
                ) + '\n\t' + '\n\t'.join([i.path for i in self._items])
            )
    
    def is_empty(self):
        return len(self._items) <= 0
    
    def get_items(self):
        return self._items
    
    def get_next(self):
        return next(self._items_cycle)
