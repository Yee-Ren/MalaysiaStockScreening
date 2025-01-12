@echo off
REM This script opens all HTML files in the current directory in the default web browser.

REM Get the current directory
set current_dir=%cd%

REM Loop through each HTML file in the directory and open it
for %%f in ("%current_dir%\*.html") do (
    echo Opening %%f
    start "" "%%f"
)

REM Wait for user to press a key before closing the script
echo All files opened. Press any key to exit.
pause > nul
