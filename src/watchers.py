from watchgod import DefaultDirWatcher

from config import config

ALLOWED_EXTENSIONS = tuple(['.' + i.lower() for i in config.ALLOWED_EXTENSIONS])


class VLCSchedulerSourceWatcher(DefaultDirWatcher):
    def should_watch_file(self, entry):
        return entry.name.endswith(ALLOWED_EXTENSIONS)
