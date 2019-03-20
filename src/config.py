import os, sys, traceback

import yaml

import defaults

CONFIG_FILENAME = 'vlcscheduler.yaml'
CONFIG_ENV_VAR = 'VLCSCHEDULER_YAML'
LOGGER_NAME = 'vlcscheduler'

config = None
logger = None


class ConfigLoadError(RuntimeError):
    pass


def locate_yaml_config():
    possible_locations = []
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        
        if os.path.basename(exe_dir) == 'MacOS' and sys.platform == 'darwin':
            possible_locations.append(os.path.join(exe_dir, '..', '..', '..'))
        else:
            possible_locations.append(exe_dir)
    else:
        src_dir = os.path.dirname(os.path.abspath(__file__))
        
        if os.path.basename(src_dir) == 'src':
            possible_locations.append(os.path.dirname(src_dir))
        else:
            possible_locations.append(src_dir)
        
        possible_locations.append(os.getcwd())
    
    possible_locations = list(set(possible_locations))
    
    for location in possible_locations:
        path = os.path.join(location, CONFIG_FILENAME)
        
        if os.path.isfile(path):
            return path
    
    raise FileNotFoundError('Cannot find the configuration file %s in any of these places: %s.' % (
        CONFIG_FILENAME, ', '.join(possible_locations))
    )


def load_yaml_config():
    path = os.getenv(CONFIG_ENV_VAR) or locate_yaml_config()
    
    with open(path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            raise ConfigLoadError('%s does not contain valid YAML.' % CONFIG_FILENAME) from e
    
    return config


def build_config():
    config = type('Config', (object,), {})()
    yaml_config = load_yaml_config()
    
    for k in [k for k in dir(defaults) if k[0:1].isupper()]:
        new_v = getattr(defaults, k)
                
        if k.lower() in yaml_config:
            usr_v = yaml_config[k.lower()]
            
            if type(new_v) is dict and type(usr_v) is dict:
                new_v = {**new_v, **usr_v}
            else:
                new_v = usr_v
        
        setattr(config, k.upper(), new_v)
    
    return config


def initialize(*args, **kwargs):
    global config, logger
    
    if config is None:
        config = build_config()
    
    if logger is None:
        try:
            import coloredlogs
        except ImportError:
            coloredlogs = None
        finally:
            import logging
        
        logger = logging.getLogger(LOGGER_NAME)
        
        params = {
            'format': '%(asctime)s %(message)s',
            'datefmt': '[%H:%M:%S]'
        }
        
        if config.DEBUG:
            params['level'] = logging.DEBUG
        else:
            params['level'] = logging.INFO
        
        if coloredlogs:
            params['fmt'] = params.pop('format')
            coloredlogs.install(**params)
        else:
            logging.basicConfig(**params)
        
        # Other loggers
        if not config.DEBUG:
            logging.getLogger('schedule').setLevel(logging.WARNING)


def check_config():
    global config
    
    if len(config.SOURCES) == 0:
        raise RuntimeError('Please define at least one source in the configuration file.')
    
    for source in config.SOURCES:
        if not os.path.isdir(source['path']):
            raise RuntimeError('The source path is not a directory: %s.' % source['path'])
        
        if source.get('special') and source.get('play_every_minutes'):
            raise RuntimeError(
                'Simultaneous use of <special> and <play_every_minutes> for a '
                'single source is currently not supported.'
            )
    
    if not os.path.isfile(config.VLC.get('path', "")):
        raise RuntimeError('Invalid path to VLC: %s.' % config.VLC.get('path', None))


try:
    initialize()
    check_config()
except Exception as e:
    if not logger:
        import logging as logger
    
    if config and not config.DEBUG:
        logger.fatal(str(e))
    else:
        logger.fatal(traceback.format_exc())
    
    sys.exit(1)
