@echo off
echo ============================================
echo Testing Whisper transcription
echo ============================================
echo.
echo Files in in/ folder:
dir /b in\*.mp4 in\*.mov in\*.wav in\*.mp3 2>nul
echo.
echo Starting transcription...
echo.
uv run python transcribe.py
echo.
echo Done! Check out/ folder for results.
pause
