import os, re

from itertools import cycle, islice, chain, filterfalse

TIME_INTERVAL_REGEX = re.compile('(\d\d:\d\d).?-.?(\d\d:\d\d)')


def list_files_with_extensions(path, extensions):
    extensions = tuple(extensions)
    
    for entry in os.scandir(path):
        if entry.name.lower().endswith(extensions) and entry.is_file():
            yield entry.path


def zip_equally(*iterables):
    # ['A1'], ['B1', 'B2', 'B3'], ['C1', 'C2'] ->
    # -> 'A1', 'B1', 'C1', 'A1', 'B2', 'C2', 'A1', 'B3', 'C1'
    if len(iterables) == 0:
        return []
    
    longest_iterable_length = len(max(iterables, key=len))
    
    iterables = [
        islice(cycle(l), longest_iterable_length) for l
        in filterfalse(lambda i: len(i) == 0, iterables)
    ]
    
    return chain(*[i for i in zip(*iterables)])


def parse_time_interval(string):
    match = TIME_INTERVAL_REGEX.match(string)
    
    if not match:
        raise ValueError
    
    return match[1], match[2]
