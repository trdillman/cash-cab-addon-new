@echo off
echo =========================================
echo CAR_TRAIL FIX TESTING SCRIPT
echo =========================================
echo.
echo This will launch Blender with test instructions
echo.
echo INSTRUCTIONS:
echo 1. When Blender opens, switch to Scripting workspace
echo 2. In Python Console, run:
echo    exec(open(r"%~dp0blender_gui_test.py").read())
echo 3. Follow the on-screen instructions
echo 4. Run the route import as instructed
echo 5. Check results with analyze_duplication()
echo.
echo Press any key to launch Blender...
pause > nul

REM Launch Blender
"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"