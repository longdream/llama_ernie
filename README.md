# 🚀 Llama ERNIE

<div align="center">

**基于 llama.cpp 的 ERNIE 4.5 模型 CPU 推理服务**

[![Rust](https://img.shields.io/badge/Rust-1.70%2B-orange.svg)](https://www.rust-lang.org/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-latest-green.svg)](https://github.com/ggerganov/llama.cpp)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-Compatible-blue.svg)](https://platform.openai.com/docs/api-reference)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[简体中文](#) | [English](README_EN.md)

</div>

---

## 📖 项目背景

百度飞桨 FastDeploy **不支持在 CPU 上推理 ERNIE 4.5 系列模型**，这给想要在纯 CPU 环境下使用 ERNIE 模型的开发者带来了困扰。本项目通过 **llama.cpp** 和 **GGUF 格式**，实现了 ERNIE 4.5 模型在 CPU 上的高效推理，提供完全兼容 OpenAI API 的服务接口。

### 🎯 核心特性

- ✅ **极简部署**: 仅需 2 个文件（5MB exe + config.toml）即可运行，无需安装依赖
- ✅ **CPU 高效推理**: 通过 llama.cpp 实现 ERNIE 4.5 模型的纯 CPU 推理
- ✅ **OpenAI API 兼容**: 完全兼容 OpenAI Chat Completions API，无需修改现有代码
- ✅ **GGUF 格式支持**: 支持量化模型（Q3_K_S、Q4_K_M、Q8_0 等），显著降低内存占用
- ✅ **动态上下文分配**: 根据实际对话长度自动分配内存，避免资源浪费
- ✅ **Embedding 支持**: 内置 BGE-M3 Embedding 模型，支持向量化操作
- ✅ **Rust 高性能**: 使用 Rust + Axum 构建，低延迟、高并发

---

## 🔥 快速开始

> 🎯 **只需 2 个文件即可运行**：一个 5MB 的 exe 文件 + 一个 config.toml 配置文件！

### 1. 环境要求

#### 运行环境（最终部署）
- **操作系统**: Windows / Linux / macOS
- **依赖**: 无需安装任何依赖！
- **模型文件**: ERNIE 4.5 GGUF 格式模型

#### 编译环境（仅首次编译需要）
- **Rust**: 1.70 或更高版本
- **编译后**: 仅需可执行文件 (5MB) + 配置文件，可复制到任意机器运行

### 2. 获取模型文件

#### 方式 1：从 ModelScope 下载（推荐，国内速度快）

```bash
# 访问 ModelScope 下载 ERNIE 4.5 GGUF 模型
# 模型库：unsloth/ERNIE-4.5-21B-A3B-PT-GGUF

# 0.3B 模型（适合测试和轻量级应用）
# https://modelscope.cn/models/unsloth/ERNIE-4.5-0.3B-PT-GGUF

# 21B 模型（多种量化版本可选）
# https://modelscope.cn/models/unsloth/ERNIE-4.5-21B-A3B-PT-GGUF
```

**可用量化版本**：
- `ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf` - Q3 量化（~8GB 内存）
- `ERNIE-4.5-21B-A3B-PT-Q4_K_M.gguf` - Q4 量化（~12GB 内存）
- `ERNIE-4.5-21B-A3B-PT-Q5_K_M.gguf` - Q5 量化（~15GB 内存）
- `ERNIE-4.5-21B-A3B-PT-Q8_0.gguf` - Q8 量化（~24GB 内存）

#### 方式 2：从 Hugging Face 下载

```bash
# 示例：ERNIE 4.5 0.3B 模型 (Q8量化)
wget https://huggingface.co/unsloth/ERNIE-4.5-0.3B-PT-GGUF/resolve/main/ernie-4.5-0.3b-pt-q8_0.gguf

# 或 ERNIE 4.5 21B 模型 (Q3量化)
wget https://huggingface.co/unsloth/ERNIE-4.5-21B-A3B-PT-GGUF/resolve/main/ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf
```

> 💡 **量化等级选择建议**：
> - **Q3_K_S**: ~8GB 内存，最快速度，适合日常对话
> - **Q4_K_M**: ~12GB 内存，平衡性能，推荐用于生产环境
> - **Q5_K_M**: ~15GB 内存，更高精度
> - **Q8_0**: ~24GB 内存，接近原始精度，适合对质量要求极高的场景

### 3. 配置文件

修改 `config.toml` 配置模型路径：

```toml
[server]
host = "0.0.0.0"
port = 8766

[model]
path = "../models/ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf"  # 修改为你的模型路径
name = "ernie-21b"

[inference]
n_ctx = 16384        # 最大上下文长度
n_threads = 10       # CPU 线程数（建议设为物理核心数）
n_gpu_layers = 0     # 纯 CPU 推理设为 0
use_mmap = true      # 使用内存映射，减少内存占用
n_batch = 512        # 批处理大小

[embedding]
model_path = "../models/bge-m3-Q4_K_M.gguf"  # Embedding 模型路径
model_name = "bge-m3"
dimension = 1024
n_ctx = 8192
n_threads = 4
```

### 4. 编译运行

#### Windows:
```bash
# 编译（仅首次需要）
build.bat

# 启动服务
start.bat
```

> 💡 **编译后只需 2 个文件**：
> - `llama_ernie_server.exe` (仅 ~5MB)
> - `config.toml` (配置文件)
> 
> 可以将这两个文件复制到任意目录运行，无需安装任何依赖！

#### Linux / macOS:
```bash
# 编译（仅首次需要）
cargo build --release

# 启动服务
./target/release/llama_ernie_server
```

> 💡 编译后的可执行文件位于 `target/release/llama_ernie_server`，仅约 5MB

### 5. 测试服务

```bash
# 健康检查
curl http://localhost:8766/health

# 模型列表
curl http://localhost:8766/v1/models

# 聊天测试
curl http://localhost:8766/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

或运行提供的测试脚本：

```bash
python test_openai_api.py
```

---

## 💻 API 使用示例

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8766/v1",
    api_key="dummy"  # 本地服务不需要真实 API Key
)

# 聊天补全
response = client.chat.completions.create(
    model="ernie-21b",
    messages=[
        {"role": "system", "content": "你是一个友好的AI助手"},
        {"role": "user", "content": "什么是人工智能？"}
    ],
    temperature=0.7,
    max_tokens=512
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl http://localhost:8766/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ernie-21b",
    "messages": [
      {"role": "system", "content": "你是一个专业的技术顾问"},
      {"role": "user", "content": "解释一下 Transformer 架构"}
    ],
    "temperature": 0.3,
    "max_tokens": 1000
  }'
```

### Embedding 向量化

```bash
curl http://localhost:8766/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一段需要向量化的文本"
  }'
```

```python
# Python 示例
import requests

response = requests.post(
    "http://localhost:8766/v1/embeddings",
    json={"text": "这是一段需要向量化的文本"}
)

embedding = response.json()["embedding"]
print(f"向量维度: {len(embedding)}")
```

---

## 🔧 高级配置

### 性能优化建议

#### CPU 线程数调优
```toml
[inference]
n_threads = 10  # 设为物理核心数（非超线程数）
```

- **8核16线程**: 设置为 8-12
- **16核32线程**: 设置为 16-20
- 过多线程会导致上下文切换开销，反而降低速度

#### 内存优化
```toml
[inference]
use_mmap = true    # 启用内存映射，减少50%+ RAM占用
n_ctx = 16384      # 根据实际需求调整（更大的上下文需要更多内存）
```

#### 模型量化选择

| 量化等级 | 内存占用 (21B) | 推理速度 | 精度损失 |
|---------|---------------|---------|---------|
| Q3_K_S  | ~8GB          | 最快    | 较大    |
| Q4_K_M  | ~12GB         | 快      | 中等    |
| Q5_K_M  | ~15GB         | 中等    | 较小    |
| Q8_0    | ~24GB         | 慢      | 极小    |

---

## 📊 性能表现

### 测试环境
- CPU: Intel i7-12700K (12核20线程)
- RAM: 32GB DDR4
- 模型: ERNIE-4.5-21B-Q3_K_S
- 配置: n_threads=10, n_ctx=16384

### 测试结果
| 场景                  | 耗时      | 速度      |
|----------------------|----------|----------|
| 简单问答 (50 tokens)  | 3.2秒    | 15.6 t/s |
| 中等回复 (200 tokens) | 12.5秒   | 16.0 t/s |
| 长文生成 (500 tokens) | 31.2秒   | 16.0 t/s |

> 💡 速度会根据 CPU 性能、模型量化等级、上下文长度等因素变化

---

## 🛣️ 路线图

- [x] **v0.1**: ERNIE 4.5 基础推理支持
- [x] **v0.2**: OpenAI API 完全兼容
- [x] **v0.3**: Embedding 模型集成
- [ ] **v0.4**: 流式输出 (SSE) 支持
- [ ] **v0.5**: 多模型管理与切换
- [ ] **v0.6**: ERNIE 4.5 微调后模型转 GGUF 工具库
- [ ] **v0.7**: 批量推理优化
- [ ] **v0.8**: GPU 加速支持 (CUDA/ROCm)
- [ ] **v0.9**: Function Calling 支持
- [ ] **v1.0**: 生产级稳定版本

---

## 🤝 贡献指南

欢迎各种形式的贡献！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发计划

我们正在开发以下功能，欢迎参与：

- **ERNIE 微调模型转换工具**: 将百度飞桨微调后的 ERNIE 模型转换为 GGUF 格式
- **模型量化工具**: 自动化 ERNIE 模型量化流程
- **性能基准测试**: 建立完整的性能测试套件

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 依赖项目

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - MIT License
- [llama-cpp-rs](https://github.com/utilityai/llama-cpp-rs) - MIT License

---

## 🙏 致谢

- 感谢 [ggerganov](https://github.com/ggerganov) 开发的 [llama.cpp](https://github.com/ggerganov/llama.cpp)
- 感谢 [utilityai](https://github.com/utilityai) 提供的 [llama-cpp-rs](https://github.com/utilityai/llama-cpp-rs) Rust 绑定
- 感谢百度飞桨团队开发的 ERNIE 系列模型

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/llama_ernie/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llama_ernie/discussions)

---

## ⚠️ 免责声明

本项目仅供学习和研究使用。使用 ERNIE 模型时，请遵守百度飞桨的使用协议和相关法律法规。

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by [Your Name]

</div>

