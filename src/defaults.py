import sys

DEBUG = 1

if getattr(sys, 'frozen', False):
    DEBUG = 0

VLC = {
    'host': '127.0.0.1',
    'port': 8080,
    'password': 'vlcremote',
    'extraintf': 'http,luaintf',
    'options': []
}

if sys.platform.startswith('win'):
    VLC['path'] = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
elif sys.platform == 'darwin':
    VLC['path'] = '/Applications/VLC.app/Contents/MacOS/VLC'
else:
    VLC['path'] = '/usr/bin/vlc'

SOURCES = []

FILENAME_WITH_A_DATE_PATTERN = '^(\d\d)-(\d\d)-(\d\d\d\d).*'

# All extensions should be lowercase and prepended with a dot
MEDIA_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.png', '.jpg')
PLAYLIST_EXTENSIONS = ('.xspf', '.m3u')

SOURCE_MIXING_FUNCTION = 'zip_equally'

IGNORE_PLAYING_TIME_IF_PLAYLIST_IS_EMPTY = False

IMAGE_PLAY_DURATION = 60

MEDIA_RECURSIVE = False
