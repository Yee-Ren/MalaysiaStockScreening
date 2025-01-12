@echo off
REM Navigate to the project directory
cd /d E:\Development\myStockScreening

REM Activate the virtual environment
call venv\Scripts\activate

REM Run the Python script
python test\test.py

REM Deactivate the virtual environment
REM deactivate

REM Pause the terminal to view any output before it closes
REM pause
