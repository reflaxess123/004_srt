@echo off
REM Quick launcher for Windows
REM Usage: run.bat video.mp4 [additional arguments]

uv run python transcribe.py %*
