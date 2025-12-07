@echo off
chcp 65001 > nul
echo ====================================
echo   编译原生 llama.cpp 测试工具
echo ====================================
echo.

REM 设置 Vulkan 环境
set "VULKAN_SDK=D:\Programs\VulkanSDK143281"
set "PATH=%VULKAN_SDK%\Bin;%PATH%"

REM 设置源码路径
set SOURCE_DIR=vendor\llama-cpp-rs\llama-cpp-sys-2\llama.cpp
if not exist "%SOURCE_DIR%" (
    echo [ERROR] 找不到 llama.cpp 源码: %SOURCE_DIR%
    pause
    exit /b 1
)

REM 创建构建目录
if not exist "build_native" mkdir build_native
cd build_native

echo [1/2] 配置 CMake (Vulkan)...
cmake ..\%SOURCE_DIR% -G "Visual Studio 17 2022" -A x64 -DGGML_VULKAN=ON
if errorlevel 1 (
    echo [ERROR] CMake 配置失败
    pause
    exit /b 1
)

echo.
echo [2/2] 编译 llama-cli...
cmake --build . --config Release --target llama-cli
if errorlevel 1 (
    echo [ERROR] 编译失败
    pause
    exit /b 1
)

echo.
echo ✅ 编译成功!
echo 可执行文件: build_native\bin\Release\llama-cli.exe
echo.
pause

