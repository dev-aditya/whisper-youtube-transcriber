@echo off
echo ========================================
echo  YouTube to Whisper Transcription UI
echo ========================================
echo.
echo Starting application...
echo.

REM Activate conda environment and run the app
call conda activate whisper
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate whisper conda environment
    echo Please make sure the 'whisper' environment exists
    pause
    exit /b 1
)

python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Application failed to start
    echo Check the error messages above
    pause
)
