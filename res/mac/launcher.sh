#!/usr/bin/osascript
tell application "Finder"
	set dir to container of (path to me)
    set bin to (dir as text) & "vlcscheduler"
end tell

tell application "Terminal"
    activate
    open bin
end tell
