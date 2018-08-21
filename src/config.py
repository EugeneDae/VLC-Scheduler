import os, sys, logging

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
        possible_locations.append(os.path.dirname(sys.executable))
    else:
        source_dir = os.path.dirname(os.path.abspath(__file__))
        
        if os.path.basename(source_dir) == 'src':
            possible_locations.append(os.path.dirname(source_dir))
        else:
            possible_locations.append(source_dir)
    
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
        logger = logging.getLogger(LOGGER_NAME)
        
        params = {
            'format': '%(asctime)s %(message)s',
            'datefmt': '[%H:%M:%S]'
        }
        
        if config.DEBUG:
            params['level'] = logging.DEBUG
        else:
            params['level'] = logging.INFO
            
        logging.basicConfig(**params)


initialize()
