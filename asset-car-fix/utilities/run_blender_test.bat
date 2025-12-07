@echo off
echo Running CashCab parent-child fix test...
echo.

REM Get Blender executable path (adjust if needed)
set BLENDER_EXE="C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"

REM Get script path
set SCRIPT_PATH=%~dp0blender_test_script.py

REM Check if Blender exists
if not exist %BLENDER_EXE% (
    echo ERROR: Blender not found at %BLENDER_EXE%
    echo Please adjust the BLENDER_EXE path in this batch file
    pause
    exit /b 1
)

REM Check if test script exists
if not exist %SCRIPT_PATH% (
    echo ERROR: Test script not found at %SCRIPT_PATH%
    pause
    exit /b 1
)

REM Run Blender with background test
echo Running Blender test script...
%BLENDER_EXE% --background --python %SCRIPT_PATH%

echo.
echo Test complete!
echo Check the test_scenes\blender_test_results folder for saved scenes.
pause