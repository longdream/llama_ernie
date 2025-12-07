@echo off
chcp 65001 > nul
echo ====================================
echo   编译 Qwen3 Llama服务 (AMD HIP/ROCm GPU)
echo ====================================
echo.

REM 设置 Visual Studio 环境
echo [1/5] 设置 Visual Studio 环境...
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 (
    echo [ERROR] 无法设置 Visual Studio 环境
    pause
    exit /b 1
)
echo ✅ Visual Studio 环境已设置

REM 设置 ROCm/HIP 环境
echo.
echo [2/5] 设置 AMD ROCm/HIP 环境...

REM 优先使用 ROCm 6.2，其次 5.7
if exist "C:\Program Files\AMD\ROCm\6.2" (
    set "HIP_PATH=C:\Program Files\AMD\ROCm\6.2"
    set "ROCM_PATH=C:\Program Files\AMD\ROCm\6.2"
    echo 检测到 ROCm 6.2
) else if exist "C:\Program Files\AMD\ROCm\5.7" (
    set "HIP_PATH=C:\Program Files\AMD\ROCm\5.7"
    set "ROCM_PATH=C:\Program Files\AMD\ROCm\5.7"
    echo 检测到 ROCm 5.7
) else (
    echo [ERROR] 未找到 ROCm 安装
    pause
    exit /b 1
)

set "PATH=%HIP_PATH%\bin;%PATH%"
echo ✅ HIP_PATH: %HIP_PATH%

REM 关键: 设置 HIP_PLATFORM 为 amd (ROCm 需要此变量)
set "HIP_PLATFORM=amd"
echo ✅ HIP_PLATFORM: %HIP_PLATFORM%

REM 设置 GPU 架构 (AMD Radeon 780M = gfx1103)
set "AMDGPU_TARGETS=gfx1103"
echo ✅ GPU架构: %AMDGPU_TARGETS%

REM 设置 Ninja 路径
echo.
echo [3/5] 配置构建工具...
if exist "tools\ninja.exe" (
    set "PATH=%CD%\tools;%PATH%"
    set "CMAKE_GENERATOR=Ninja"
    echo ✅ 使用 Ninja 构建系统
) else (
    echo [WARNING] 未找到 Ninja，将使用默认构建系统
)

REM 解决 Windows 路径过长问题
set "CARGO_TARGET_DIR=D:\t"
if not exist "%CARGO_TARGET_DIR%" mkdir "%CARGO_TARGET_DIR%"
echo 构建目录: %CARGO_TARGET_DIR%

REM 清理旧的构建缓存（切换后端时需要）
if exist "%CARGO_TARGET_DIR%\release\build\llama-cpp-sys-2*" (
    echo.
    echo [3.5/5] 清理旧的构建缓存...
    rmdir /s /q "%CARGO_TARGET_DIR%\release\build" 2>nul
    echo ✅ 缓存已清理
)

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
echo [5/5] 编译 Release 版本 (AMD HIP/ROCm GPU 支持)...
echo 注意: 首次编译可能需要 15-30 分钟
echo.

cargo build --release

if errorlevel 1 (
    echo.
    echo [ERROR] 编译失败，请检查错误信息
    echo.
    echo 常见问题:
    echo   1. 确保 ROCm 已正确安装
    echo   2. 确保 hipcc 在 PATH 中
    echo   3. 检查 AMDGPU_TARGETS 是否正确
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
echo ✅ 编译成功！(AMD HIP/ROCm GPU 支持)
echo ====================================
echo.
echo 生成文件: llama_qwen.exe
for %%F in (llama_qwen.exe) do echo 文件大小: %%~zF 字节
echo.
echo 使用方法:
echo   1. 确保 config.toml 中 n_gpu_layers 设置正确
echo   2. 运行: start.bat 或 llama_qwen.exe
echo.
echo GPU架构: gfx1103 (AMD Radeon 780M)
echo ROCm版本: %HIP_PATH%
echo.
pause

