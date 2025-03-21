@echo off
REM This batch file runs the Voice Assistant from the current directory
TITLE Windows Voice Assistant

REM Attempt to find Python in common locations
SET PYTHON_CMD=python
WHERE %PYTHON_CMD% >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    SET PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    IF NOT EXIST "%PYTHON_CMD%" (
        SET PYTHON_CMD=%PROGRAMFILES%\Python311\python.exe
        IF NOT EXIST "%PYTHON_CMD%" (
            ECHO Python not found. Please ensure Python is installed and in your PATH.
            PAUSE
            EXIT /B 1
        )
    )
)

ECHO Starting Windows Voice Assistant...

REM Run the assistant in background
START /B "" "%PYTHON_CMD%" "%~dp0main.py"

ECHO Setting up the assistant... You will receive a notification when it is ready.
ECHO You can close this window now.