@echo off
del dist\vlcscheduler.exe
call venv\Scripts\activate
venv\Scripts\pyinstaller --onefile --icon="res\win\Icon.ico" src\vlcscheduler.py
