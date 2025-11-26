@echo off
echo Starting Daphne WebSocket server...

cd %~dp0

CALL my_venv\Scripts\activate

daphne -b 0.0.0.0 -p 8001 job_portal.asgi:application

pause

