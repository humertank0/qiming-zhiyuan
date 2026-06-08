@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$env:PYTHONIOENCODING='utf-8'; python agent.py; Read-Host '按回车退出'"
