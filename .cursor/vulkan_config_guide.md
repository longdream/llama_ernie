# Vulkan GPU 加速配置指南

## 📝 配置概览

项目已成功配置 Vulkan GPU 加速支持，可使用 Intel Arc GPU 或其他 Vulkan 兼容 GPU 进行推理加速。

## ✅ 已完成的配置

### 1. Cargo.toml 修改
启用了 `llama-cpp-2` 的 Vulkan 特性：

```toml
llama-cpp-2 = { path = "vendor/llama-cpp-rs/llama-cpp-2", features = ["vulkan"] }
```

### 2. config.toml 修改

#### 模型路径更新
```toml
[model]
path = "D:\\models\\Qwen3-30B-A3B-Instruct-2507-Q3_K_S.gguf"
name = "qwen3-30b"
```

#### GPU 层配置
```toml
[inference]
n_gpu_layers = 48  # Qwen3-30B-A3B 共 48 层，全部放到 GPU
```

## 🚀 编译和运行

### 编译（带 Vulkan 支持）

**Windows:**
```bash
build_vulkan.bat
```

这将：
1. 设置 Visual Studio 环境
2. 配置 Vulkan SDK（路径：C:\VulkanSDK\1.4.328.1）
3. 编译 Release 版本（首次编译 Vulkan 着色器需要 10-15 分钟）
4. 生成 `llama_qwen.exe`

**Linux/macOS:**
```bash
cargo build --release --features vulkan
```

### 运行服务

```bash
# Windows
start.bat

# 或直接运行
llama_qwen.exe
```

## ⚙️ 性能优化参数说明

### GPU 层数配置 (n_gpu_layers)

| 值 | 说明 | 适用场景 |
|---|---|---|
| 0 | 纯 CPU 推理 | 无 GPU 或测试 |
| 24 | 一半层在 GPU | 显存不足时 |
| 48 | 全部层在 GPU（推荐） | 最快速度，需足够显存 |
| -1 | 自动最大化 GPU 使用 | 让系统自动决定 |

### 上下文长度 (n_ctx)

当前配置：`n_ctx = 16384`

- **4096**: 轻量级对话
- **8192**: 标准任务
- **16384**: 复杂任务（推荐）
- **32768+**: 超长上下文（需要更多显存）

### 线程数 (n_threads)

当前配置：`n_threads = 10`

使用 GPU 时，CPU 线程主要用于数据预处理：
- **8-12**: 对于 8 核 CPU
- **16-20**: 对于 16 核 CPU

## 📊 预期性能提升

使用 Vulkan GPU 加速后，相比纯 CPU：

| 指标 | CPU 模式 | Vulkan GPU 模式 | 提升 |
|---|---|---|---|
| 推理速度 | ~16 tokens/s | ~50-100 tokens/s | 3-6倍 |
| 首 token 延迟 | 较高 | 显著降低 | 2-4倍 |
| 内存占用 | ~12GB RAM | ~8GB RAM + 4GB VRAM | 分担负载 |

*实际性能取决于具体 GPU 型号和驱动版本*

## 🔍 验证配置

### 1. 检查 Vulkan SDK
```bash
echo %VULKAN_SDK%
# 应输出: C:\VulkanSDK\1.4.328.1
```

### 2. 检查模型文件
```bash
dir D:\models\Qwen3-30B-A3B-Instruct-2507-Q3_K_S.gguf
# 应显示文件存在，大小约 12-13 GB
```

### 3. 启动服务测试
```bash
# 启动服务
llama_qwen.exe

# 另一个终端测试
curl http://localhost:8766/health
curl http://localhost:8766/v1/models
```

### 4. 推理测试
```bash
curl http://localhost:8766/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"你好，请介绍一下你自己\"}], \"max_tokens\": 100}"
```

观察日志，应该看到类似：
- `Using Vulkan GPU backend`
- `GPU layers: 48/48`
- 推理速度显著提升

## ⚠️ 常见问题

### 1. 编译时找不到 Vulkan SDK
**解决方案**: 检查 `build_vulkan.bat` 中的 SDK 路径是否正确
```batch
set VULKAN_SDK=C:\VulkanSDK\1.4.328.1
```

### 2. 运行时显存不足
**解决方案**: 降低 `n_gpu_layers` 或 `n_ctx`
```toml
n_gpu_layers = 24  # 一半层
n_ctx = 8192       # 减小上下文
```

### 3. 推理速度没有提升
**可能原因**:
- GPU 层数设置为 0（检查 config.toml）
- Vulkan 驱动未正确安装
- 编译时未启用 Vulkan 特性（检查是否使用 build_vulkan.bat）

### 4. 模型文件找不到
**解决方案**: 
- 确认文件路径：`D:\models\Qwen3-30B-A3B-Instruct-2507-Q3_K_S.gguf`
- Windows 路径需要双反斜杠：`D:\\models\\...`

## 📚 技术栈

- **Rust**: 高性能服务器
- **llama.cpp**: GGUF 模型推理引擎
- **Vulkan**: 跨平台 GPU 加速 API
- **Qwen3-30B-A3B**: 混合专家模型（30.53B 参数，Q3_K 量化）

## 🎯 下一步

1. **性能调优**: 根据实际使用情况调整 `n_gpu_layers` 和 `n_ctx`
2. **监控**: 使用 GPU-Z 或 Task Manager 监控 GPU 使用率
3. **测试**: 运行 `test_qwen_speed.py` 进行性能基准测试
4. **部署**: 如果性能满意，可以将配置固化用于生产环境

## 📖 参考资料

- [llama.cpp Vulkan 后端文档](https://github.com/ggerganov/llama.cpp/blob/master/docs/backend/VULKAN.md)
- [Vulkan SDK 下载](https://vulkan.lunarg.com/sdk/home)
- [Qwen 模型文档](https://github.com/QwenLM/Qwen)

---

**配置完成时间**: 2025-12-07
**配置目标**: Vulkan GPU 加速 + Qwen3-30B-A3B 模型推理
**状态**: ✅ 已完成，待编译测试

