@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0open_knowledge_distillation.ps1"
