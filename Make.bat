@echo off
del dist\vlcscheduler.exe
call venv\Scripts\activate
venv\Scripts\pyinstaller --onefile --icon="src\resources\vlc.ico" src\vlcscheduler.py
