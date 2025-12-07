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

REM 预先设置构建输出目录（缩短路径，避免 MAX_PATH）
set "CARGO_TARGET_DIR=D:\t"
if not exist "%CARGO_TARGET_DIR%" mkdir "%CARGO_TARGET_DIR%"
echo 构建目录重定向至: %CARGO_TARGET_DIR%

REM 设置 Vulkan SDK 环境（自动检测）
echo.
echo [2/4] 设置 Vulkan SDK 环境...

REM 尝试检测已安装的 Vulkan SDK
if defined VULKAN_SDK (
    echo 检测到环境变量: %VULKAN_SDK%
) else if exist "C:\VulkanSDK\1.4.328.1" (
    set VULKAN_SDK=C:\VulkanSDK\1.4.328.1
    echo 检测到版本: 1.4.328.1
) else if exist "D:\Programs\VulkanSDK143281" (
    set VULKAN_SDK=D:\Programs\VulkanSDK143281
    echo 检测到用户指定路径: D:\Programs\VulkanSDK143281
) else if exist "C:\VulkanSDK" (
    for /f "delims=" %%i in ('dir /b /ad "C:\VulkanSDK" 2^>nul ^| sort /r') do (
        set VULKAN_SDK=C:\VulkanSDK\%%i
        goto :vulkan_found
    )
) else (
    echo [WARNING] 未找到 Vulkan SDK，将使用系统 Vulkan 运行时
    echo 如需完整开发支持，请从 https://vulkan.lunarg.com/ 下载安装
    set VULKAN_SDK=
    goto :skip_vulkan_sdk
)

:vulkan_found
if defined VULKAN_SDK (
    set "PATH=%VULKAN_SDK%\Bin;%PATH%"
    echo ✅ Vulkan SDK: %VULKAN_SDK%
)

:skip_vulkan_sdk

REM 设置 Ninja 路径（解决 Windows 路径过长导致 MSBuild 失败的问题）
if exist "tools\ninja.exe" (
    set "PATH=%CD%\tools;%PATH%"
    set "CMAKE_GENERATOR=Ninja"
    set "CMAKE_MAKE_PROGRAM=%CD%\tools\ninja.exe"
    echo [INFO] 使用 Ninja 构建系统: tools\ninja.exe
    
    REM === 关键修复：强制清理旧的 CMake 缓存 ===
    if exist "%CARGO_TARGET_DIR%\release\build" (
        echo [INFO] 清理旧的 CMake 缓存以启用 Ninja...
        rmdir /s /q "%CARGO_TARGET_DIR%\release\build"
    )
) else (
    echo [WARNING] 未找到 Ninja，将回退到 MSBuild (可能遇到路径过长错误)
)

REM 强制设置 CMake 参数以确保启用 Vulkan
set "CMAKE_ARGS=-DGGML_VULKAN=ON -DGGML_VULKAN_SDK=%VULKAN_SDK%"
echo CMAKE_ARGS: %CMAKE_ARGS%

REM 解决 Windows 路径过长问题 (MAX_PATH 260字符限制)
REM 将构建目录指向盘符根目录下的短路径

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
if exist "%CARGO_TARGET_DIR%\release\llama_qwen_server.exe" (
    copy "%CARGO_TARGET_DIR%\release\llama_qwen_server.exe" llama_qwen.exe >nul
    echo ✅ 可执行文件已复制
) else (
    echo [ERROR] 未找到编译产物: %CARGO_TARGET_DIR%\release\llama_qwen_server.exe
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

