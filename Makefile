UNAME := $(shell uname)

PYINSTALLER = venv/bin/pyinstaller
PLIST_BUDDY = /usr/libexec/PlistBuddy -c

TARGET_APP = dist/VLC\ Scheduler.app
TARGET_BIN = dist/vlcscheduler

VERSION := `cd src && python -c "import version as v; print(v.VERSION)"`
INFO_PLIST := $(TARGET_APP)/Contents/Info.plist

all:
ifeq ($(UNAME), Linux)
	@make $(TARGET_BIN)
endif	
ifeq ($(UNAME), Darwin)
	@make $(TARGET_APP)
endif

$(TARGET_APP): $(TARGET_BIN)
	rm -rf $(TARGET_APP)
	mkdir -p $(TARGET_APP)/Contents/{MacOS,Resources}/
	cp $(TARGET_BIN) $(TARGET_APP)/Contents/MacOS
	cp res/mac/Info.plist $(INFO_PLIST)
	cp res/mac/launcher.sh $(TARGET_APP)/Contents/MacOS/
	cp res/mac/Icon.icns $(TARGET_APP)/Contents/Resources/
	$(PLIST_BUDDY) "Add CFBundleVersion String $(VERSION)" $(INFO_PLIST)

$(TARGET_BIN): src/
	$(PYINSTALLER) --clean --onefile src/vlcscheduler.py

clean:
	rm -rf 'vlcscheduler.spec' 'build' $(TARGET_BIN) $(TARGET_APP)

.PHONY: all clean
