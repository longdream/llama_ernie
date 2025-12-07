@echo off
chcp 65001 > nul
echo ====================================
echo   编译 Qwen3 Llama服务 (OpenCL GPU)
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

REM 设置 OpenCL SDK 环境
echo.
echo [2/4] 配置 OpenCL SDK...
set "OPENCL_SDK=%CD%\tools\OpenCL-SDK\OpenCL-SDK-v2024.10.24-Win-x64"
if not exist "%OPENCL_SDK%" (
    echo [ERROR] OpenCL SDK 未找到: %OPENCL_SDK%
    pause
    exit /b 1
)
set "OpenCL_ROOT=%OPENCL_SDK%"
set "OPENCL_ROOT=%OPENCL_SDK%"
set "OpenCL_INCLUDE_DIR=%OPENCL_SDK%\include"
set "OpenCL_LIBRARY=%OPENCL_SDK%\lib\OpenCL.lib"
echo ✅ OpenCL SDK: %OPENCL_SDK%

REM 设置 Ninja 路径
echo.
echo [3/4] 配置构建工具...
if exist "tools\ninja.exe" (
    set "PATH=%CD%\tools;%PATH%"
    set "CMAKE_GENERATOR=Ninja"
    echo ✅ 使用 Ninja 构建系统
)

REM 解决 Windows 路径过长问题
set "CARGO_TARGET_DIR=D:\t"
if not exist "%CARGO_TARGET_DIR%" mkdir "%CARGO_TARGET_DIR%"
echo 构建目录: %CARGO_TARGET_DIR%

REM 清理旧的构建缓存（切换后端时需要）
if exist "%CARGO_TARGET_DIR%\release\build\llama-cpp-sys-2*" (
    echo.
    echo 清理旧的构建缓存...
    rmdir /s /q "%CARGO_TARGET_DIR%\release\build" 2>nul
    echo ✅ 缓存已清理
)

REM 设置 CMake 参数 - 强制启用 OpenCL
set "CMAKE_ARGS=-DGGML_OPENCL=ON -DOpenCL_ROOT=%OPENCL_SDK% -DOpenCL_INCLUDE_DIR=%OPENCL_SDK%\include -DOpenCL_LIBRARY=%OPENCL_SDK%\lib\OpenCL.lib"
echo CMAKE_ARGS: %CMAKE_ARGS%

REM 检查 Rust 环境
echo.
echo [4/5] 检查 Rust 环境...
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
echo [5/5] 编译 Release 版本 (OpenCL GPU 支持)...
echo 注意: 首次编译可能需要 10-20 分钟
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
    echo [ERROR] 未找到编译产物
    pause
    exit /b 1
)

echo.
echo ====================================
echo ✅ 编译成功！(OpenCL GPU 支持)
echo ====================================
echo.
echo 生成文件: llama_qwen.exe
for %%F in (llama_qwen.exe) do echo 文件大小: %%~zF 字节
echo.
echo 使用方法:
echo   1. 确保 config.toml 中 n_gpu_layers 设置正确
echo   2. 运行: start.bat 或 llama_qwen.exe
echo.
pause

