@echo off
chcp 65001 > nul
echo ====================================
echo   启动 Qwen3 Llama服务 (Vulkan GPU)
echo ====================================
echo.

REM 设置 Vulkan 环境 (根据你提供的路径)
set "VULKAN_SDK=D:\Programs\VulkanSDK143281"
set "PATH=%VULKAN_SDK%\Bin;%PATH%"

REM 强制使用 Vulkan 设备 0 (通常是独立显卡或高性能集显)
set GGML_VULKAN_DEVICE=0

REM 开启 Vulkan 调试日志
set GGML_VULKAN_DEBUG=1
set GGML_VULKAN_PERF=1

REM 设置日志级别
set RUST_LOG=info,llama_cpp_2=info

echo [配置信息]
echo VULKAN_SDK: %VULKAN_SDK%
echo GGML_VULKAN_DEVICE: %GGML_VULKAN_DEVICE%
echo.

REM 检查exe是否存在
if not exist "llama_qwen.exe" (
    echo [ERROR] 未找到 llama_qwen.exe
    echo.
    echo 请先编译项目:
    echo   方式1: 运行 build_vulkan.bat
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
)
echo ====================================
echo.

echo 🚀 启动服务...
echo 📝 日志文件: logs\service.log
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动服务并同时输出到控制台和日志文件
powershell -Command "& { .\llama_qwen.exe 2>&1 | Tee-Object -FilePath 'logs\service.log' }"
