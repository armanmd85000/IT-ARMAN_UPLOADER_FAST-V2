@echo off
TITLE DRM Bot
:loop
echo Starting Bot...
pip install -r requirements.txt
python main.py
echo Bot stopped or crashed, restarting in 5 seconds...
timeout /t 5
goto loop
