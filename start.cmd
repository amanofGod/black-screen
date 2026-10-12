@echo off
cd /d "%~dp0"
python -B background_input.py
if errorlevel 1 pause
