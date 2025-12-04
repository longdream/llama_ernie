@echo off
chcp 65001 > nul
echo ====================================
echo   编译 Qwen3 Llama服务 (Vulkan GPU)
echo ====================================
echo.

REM 设置 Visual Studio 环境
echo [1/4] 设置 Visual Studio 环境...
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 (
    echo [ERROR] 无法设置 Visual Studio 环境
    pause
    exit /b 1
)
echo ✅ Visual Studio 环境已设置

REM 设置 Vulkan SDK 环境
echo.
echo [2/4] 设置 Vulkan SDK 环境...
set VULKAN_SDK=C:\VulkanSDK\1.4.328.1
if not exist "%VULKAN_SDK%" (
    echo [ERROR] Vulkan SDK 未找到: %VULKAN_SDK%
    pause
    exit /b 1
)
set PATH=%VULKAN_SDK%\Bin;%PATH%
echo ✅ Vulkan SDK: %VULKAN_SDK%

REM 检查 Rust 环境
echo.
echo [3/4] 检查 Rust 环境...
rustc --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未安装 Rust
    pause
    exit /b 1
)
rustc --version
echo ✅ Rust 环境正常

REM 编译
echo.
echo [4/4] 编译 Release 版本 (Vulkan GPU 支持)...
echo 注意: 首次编译 Vulkan 着色器可能需要 10-15 分钟
echo.

cargo build --release

if errorlevel 1 (
    echo.
    echo [ERROR] 编译失败，请检查错误信息
    pause
    exit /b 1
)

REM 复制可执行文件
echo.
echo 复制可执行文件...
if exist "target\release\llama_qwen_server.exe" (
    copy target\release\llama_qwen_server.exe llama_qwen.exe >nul
    echo ✅ 可执行文件已复制
) else (
    echo [ERROR] 未找到编译产物
    pause
    exit /b 1
)

echo.
echo ====================================
echo ✅ 编译成功！(Vulkan GPU 支持)
echo ====================================
echo.
echo 生成文件: llama_qwen.exe
for %%F in (llama_qwen.exe) do echo 文件大小: %%~zF 字节
echo.
echo 📚 使用方法:
echo   1. 确保模型文件在当前目录
echo   2. 修改 config.toml 设置 n_gpu_layers = 48
echo   3. 运行: llama_qwen.exe
echo.
echo 💡 提示: 
echo   - 已启用 Vulkan GPU 加速 (Intel Arc 140V)
echo   - 设置 n_gpu_layers 控制 GPU 层数
echo.
pause

