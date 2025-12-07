@echo off
echo Cleaning Python cache folders...
echo.

:: Count initial __pycache__ directories
set count=0
for /f %%i in ('dir /s /b /a:d __pycache__ 2^>nul ^| find /c /v ""') do set count=%%i
echo Found %count% __pycache__ directories
echo.

:: Remove all __pycache__ directories
if %count% gtr 0 (
    echo Removing __pycache__ directories...
    for /d /r %%d in (__pycache__) do (
        if exist "%%d" (
            echo Removing: %%d
            rmdir /s /q "%%d"
        )
    )
    echo.
) else (
    echo No __pycache__ directories found.
)

:: Verify removal
set remaining=0
for /f %%i in ('dir /s /b /a:d __pycache__ 2^>nul ^| find /c /v ""') do set remaining=%%i

if %remaining% equ 0 (
    echo SUCCESS: All __pycache__ directories removed!
) else (
    echo WARNING: %remaining% __pycache__ directories remain.
)

echo.
echo Cleaning complete!
pause