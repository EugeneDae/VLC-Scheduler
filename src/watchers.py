from watchgod import DefaultDirWatcher

from config import config


class VLCSchedulerSourceWatcher(DefaultDirWatcher):
    allowed_extensions = tuple(list(config.MEDIA_EXTENSIONS) + list(config.PLAYLIST_EXTENSIONS))
    
    def should_watch_file(self, entry):
        return entry.name.lower().endswith(self.allowed_extensions)
