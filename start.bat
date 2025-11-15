@echo off
chcp 65001 > nul
echo ====================================
echo   ERNIE 0.3B Llama服务 (Rust)
echo   OpenAI兼容API
echo ====================================
echo.

REM 检查exe是否存在
if not exist "llama_ernie_server.exe" (
    echo [ERROR] 未找到 llama_ernie_server.exe
    echo.
    echo 请先编译项目:
    echo   方式1: 运行 build.bat
    echo   方式2: 执行 cargo build --release
    echo.
    pause
    exit /b 1
)

REM 读取并显示配置信息
echo 📋 配置信息:
echo ====================================
if exist "config.toml" (
    findstr /C:"path = " config.toml | findstr /C:"model"
    findstr /C:"name = " config.toml | findstr /C:"model"
    findstr /C:"n_ctx = " config.toml
    findstr /C:"n_threads = " config.toml
    findstr /C:"n_gpu_layers = " config.toml
) else (
    echo   使用默认配置
)
echo ====================================
echo.

echo 🚀 启动服务...
echo.
echo 📡 服务信息:
echo   - 监听地址: http://0.0.0.0:8766
echo   - 健康检查: http://localhost:8766/health
echo   - 模型列表: http://localhost:8766/v1/models
echo   - 聊天端点: http://localhost:8766/v1/chat/completions
echo   - Embedding: http://localhost:8766/v1/embeddings
echo.
echo 📝 日志文件: logs\service.log
echo 💡 提示: 按 Ctrl+C 停止服务
echo ====================================
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动服务并同时输出到控制台和日志文件
REM 使用 PowerShell 实现 tee 功能
powershell -Command "& { .\llama_ernie_server.exe 2>&1 | Tee-Object -FilePath 'logs\service.log' }"
