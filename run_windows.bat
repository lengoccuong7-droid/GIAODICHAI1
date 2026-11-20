@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\streamlit.exe (
  echo Chua cai moi truong. Hay chay install_windows.bat truoc.
  pause
  exit /b 1
)
call .venv\Scripts\activate
streamlit run app.py
