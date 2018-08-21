@echo off
del dist\vlcscheduler.exe
call src\venv\Scripts\activate
src\venv\Scripts\pyinstaller --onefile --icon="src\resources\vlc.ico" src\vlcscheduler.py
