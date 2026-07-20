@echo off
chcp 65001 >nul
title 简历专家
cd /d "%~dp0"
echo 正在检查运行环境...
"C:\Users\admin\AppData\Local\Programs\Python\Python313\python.exe" -c "import flask, flask_sqlalchemy, requests" 2>nul
if errorlevel 1 (
  echo 首次运行，正在安装依赖...
  "C:\Users\admin\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
)
echo 正在启动简历专家...
start "" http://localhost:5463
"C:\Users\admin\AppData\Local\Programs\Python\Python313\python.exe" server.py
pause
