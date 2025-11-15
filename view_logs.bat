@echo off
chcp 65001 > nul
echo ====================================
echo   查看服务日志
echo ====================================
echo.

if not exist "logs\service.log" (
    echo [ERROR] 未找到日志文件: logs\service.log
    echo.
    echo 请先启动服务（运行 start.bat）
    echo.
    pause
    exit /b 1
)

echo 📝 显示最新日志（最后100行）
echo ====================================
echo.

REM 显示最后100行日志
powershell -Command "Get-Content -Path 'logs\service.log' -Tail 100"

echo.
echo ====================================
echo 💡 提示:
echo   - 完整日志文件: logs\service.log
echo   - 可用记事本打开查看: notepad logs\service.log
echo ====================================
echo.

pause

