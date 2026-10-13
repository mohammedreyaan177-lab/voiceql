@echo off
title VoiceQL Django Server

cd /d "%~dp0"

set DJANGO_SETTINGS_MODULE=config.development_settings

echo Starting VoiceQL backend...
echo Using development settings.
echo.

uv run python manage.py runserver 127.0.0.1:8000

pause
