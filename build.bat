@echo off
chcp 65001 > nul
echo ====================================
echo   编译 ERNIE 0.3B Llama服务 (Rust)
echo ====================================
echo.

echo [1/3] 检查Rust环境...
rustc --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未安装Rust
    echo 请访问 https://rustup.rs/ 安装Rust
    pause
    exit /b 1
)
rustc --version
echo ✅ Rust环境正常

echo.
echo [2/3] 编译Release版本...
echo 注意: 首次编译需要下载依赖，可能需要5-10分钟
echo.

cargo build --release

if errorlevel 1 (
    echo.
    echo [ERROR] 编译失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo [3/3] 复制可执行文件...
if exist "target\release\llama_ernie_server.exe" (
    copy target\release\llama_ernie_server.exe llama_ernie_server.exe >nul
    echo ✅ 可执行文件已复制
) else (
    echo [ERROR] 未找到编译产物
    pause
    exit /b 1
)

echo.
echo ====================================
echo ✅ 编译成功！
echo ====================================
echo.
echo 生成文件: llama_ernie_server.exe
for %%F in (llama_ernie_server.exe) do echo 文件大小: %%~zF 字节 (%%~zF / 1024 / 1024 MB)
echo.
echo 📚 使用方法:
echo   1. 确保模型文件在 ../models/ernie-4.5-0.3b-pt-q8_0.gguf
echo   2. 运行: start.bat 或 llama_ernie_server.exe
echo   3. 访问: http://localhost:8766/health
echo.
echo 💡 提示: 可以直接分发 llama_ernie_server.exe，无需Rust环境
echo.
pause
