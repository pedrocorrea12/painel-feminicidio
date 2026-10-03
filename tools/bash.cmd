@echo off
rem Windows compatibility shim for the Sites packager's bash entrypoint.
if "%~2"=="" exit /b 64
if "%~3"=="" exit /b 64
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0sites-package.ps1" -Project "%~2" -Archive "%~3"
