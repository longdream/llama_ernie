@echo off
chcp 65001 > nul
echo ====================================
echo   当前配置信息
echo ====================================
echo.

if not exist "config.toml" (
    echo [ERROR] 未找到 config.toml 配置文件
    pause
    exit /b 1
)

echo 🤖 LLM 模型配置:
echo ====================================
findstr /C:"path = " config.toml | findstr /V "embedding"
findstr /C:"name = " config.toml | findstr /V "embedding"
echo.

echo ⚙️  推理参数:
echo ====================================
findstr /C:"n_ctx = " config.toml
findstr /C:"n_threads = " config.toml
findstr /C:"n_gpu_layers = " config.toml
findstr /C:"use_mmap = " config.toml
findstr /C:"n_batch = " config.toml
echo.

echo 🔢 Embedding 模型配置:
echo ====================================
findstr /C:"model_path = " config.toml
findstr /C:"model_name = " config.toml
findstr /C:"dimension = " config.toml
echo.

echo 🌐 服务配置:
echo ====================================
findstr /C:"host = " config.toml
findstr /C:"port = " config.toml
echo.

echo ====================================
echo 💡 提示:
echo   - 修改配置请编辑 config.toml
echo   - 修改后需重启服务生效
echo ====================================
echo.

pause

