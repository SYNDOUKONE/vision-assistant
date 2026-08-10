@echo off
TITLE V.I.S.I.O.N — Backend IA
COLOR 0A
cd /d "%~dp0"

:RESTART
echo.
echo [%TIME%] ============================================================
echo [%TIME%]    V.I.S.I.O.N  — Demarrage du backend...
echo [%TIME%] ============================================================
echo.
".\\venv\\Scripts\\python.exe" -u "main_v2.py"
echo.
echo [%TIME%] Backend arrete. Relancement dans 3 secondes...
ping -n 4 127.0.0.1 >nul
goto RESTART
