@echo off
chcp 65001 >nul
echo ========================================
echo   舆情分析平台 一键启动
echo ========================================

echo [1/2] 启动后端 (http://127.0.0.1:8000) ...
start "sentiment-backend" cmd /c "cd /d %~dp0backend && python run.py"

echo [2/2] 启动前端 (http://127.0.0.1:5173) ...
start "sentiment-frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo 等待服务就绪 ...
timeout /t 8 /nobreak >nul

echo.
echo 启动完成！
echo   前端: http://127.0.0.1:5173
echo   后端: http://127.0.0.1:8000/docs
echo   演示账号: analyst / analyst123
echo.
start http://127.0.0.1:5173
