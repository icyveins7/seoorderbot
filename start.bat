@echo off
:loop
python seopibot_main.py

if ERRORLEVEL 1 echo Restarting the bot.. & goto loop

if ERRORLEVEL 0 echo Full exit requested.
