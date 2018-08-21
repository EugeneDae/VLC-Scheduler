import sys

DEBUG = 0

VLC = {
    'launch': True,
    'host': '127.0.0.1',
    'port': 8080,
    'password': 'vlcremote'
}

if sys.platform.startswith('win'):
    VLC['path'] = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
elif sys.platform == 'darwin':
    VLC['path'] = '/Applications/VLC.app/Contents/MacOS/VLC'

SOURCES = []

FILENAME_WITH_A_DATE_REGEX = '^(\d\d)-(\d\d)-(\d\d\d\d).*'

ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov']

REBUILD_DELAY = 30

MIXING_FUNCTION = 'chain'
