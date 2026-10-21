@echo off
chcp 65001 >nul
set "PY=C:\Users\Ilya\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe"
if not exist "%PY%" set "PY=C:\Users\Ilya\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
start "" "%PY%" "%~dp0app.py"
