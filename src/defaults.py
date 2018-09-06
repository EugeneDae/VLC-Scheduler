import sys

DEBUG = 1

if getattr(sys, 'frozen', False):
    DEBUG = 0

VLC = {
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

ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'png', 'jpg']

SOURCE_MIXING_FUNCTION = 'zip_equally'

IGNORE_PLAYING_TIME_IF_PLAYLIST_IS_EMPTY = False

IMAGE_PLAY_DURATION = 60
