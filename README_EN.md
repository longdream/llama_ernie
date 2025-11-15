# 🚀 Llama ERNIE

<div align="center">

**CPU Inference Service for ERNIE 4.5 Models Based on llama.cpp**

[![Rust](https://img.shields.io/badge/Rust-1.70%2B-orange.svg)](https://www.rust-lang.org/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-latest-green.svg)](https://github.com/ggerganov/llama.cpp)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-Compatible-blue.svg)](https://platform.openai.com/docs/api-reference)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](#) | [简体中文](README.md)

</div>

---

## 📖 Background

Baidu PaddlePaddle's FastDeploy **does not support CPU inference for ERNIE 4.5 models**, which is a challenge for developers who want to use ERNIE models in pure CPU environments. This project enables efficient CPU inference of ERNIE 4.5 models through **llama.cpp** and **GGUF format**, providing a fully OpenAI API-compatible service interface.

### 🎯 Key Features

- ✅ **Ultra-Lightweight Deployment**: Only 2 files needed (5MB exe + config.toml), no dependencies required
- ✅ **Efficient CPU Inference**: Pure CPU inference for ERNIE 4.5 models via llama.cpp
- ✅ **OpenAI API Compatible**: Fully compatible with OpenAI Chat Completions API, no code changes needed
- ✅ **GGUF Format Support**: Supports quantized models (Q3_K_S, Q4_K_M, Q8_0, etc.), significantly reducing memory usage
- ✅ **Dynamic Context Allocation**: Automatically allocates memory based on actual conversation length, avoiding resource waste
- ✅ **Embedding Support**: Built-in BGE-M3 Embedding model for vectorization operations
- ✅ **High-Performance Rust**: Built with Rust + Axum for low latency and high concurrency

---

## 🔥 Quick Start

> 🎯 **Only 2 files needed to run**: One 5MB exe file + one config.toml configuration file!

### 1. Requirements

#### Runtime Environment (Final Deployment)
- **OS**: Windows / Linux / macOS
- **Dependencies**: No dependencies required!
- **Model Files**: ERNIE 4.5 models in GGUF format

#### Build Environment (Only needed for first-time compilation)
- **Rust**: 1.70 or higher
- **After compilation**: Only executable (5MB) + config file needed, can be copied to any machine

### 2. Get Model Files

#### Option 1: Download from ModelScope (Recommended for China, faster)

```bash
# Visit ModelScope to download ERNIE 4.5 GGUF models
# Model repository: unsloth/ERNIE-4.5-21B-A3B-PT-GGUF

# 0.3B model (suitable for testing and lightweight applications)
# https://modelscope.cn/models/unsloth/ERNIE-4.5-0.3B-PT-GGUF

# 21B model (multiple quantization versions available)
# https://modelscope.cn/models/unsloth/ERNIE-4.5-21B-A3B-PT-GGUF
```

**Available Quantization Versions**:
- `ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf` - Q3 quantized (~8GB RAM)
- `ERNIE-4.5-21B-A3B-PT-Q4_K_M.gguf` - Q4 quantized (~12GB RAM)
- `ERNIE-4.5-21B-A3B-PT-Q5_K_M.gguf` - Q5 quantized (~15GB RAM)
- `ERNIE-4.5-21B-A3B-PT-Q8_0.gguf` - Q8 quantized (~24GB RAM)

#### Option 2: Download from Hugging Face

```bash
# Example: ERNIE 4.5 0.3B model (Q8 quantized)
wget https://huggingface.co/unsloth/ERNIE-4.5-0.3B-PT-GGUF/resolve/main/ernie-4.5-0.3b-pt-q8_0.gguf

# Or ERNIE 4.5 21B model (Q3 quantized)
wget https://huggingface.co/unsloth/ERNIE-4.5-21B-A3B-PT-GGUF/resolve/main/ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf
```

> 💡 **Quantization Level Recommendations**:
> - **Q3_K_S**: ~8GB RAM, fastest speed, suitable for daily conversations
> - **Q4_K_M**: ~12GB RAM, balanced performance, recommended for production
> - **Q5_K_M**: ~15GB RAM, higher accuracy
> - **Q8_0**: ~24GB RAM, near-original accuracy, suitable for high-quality requirements

### 3. Configuration

Edit `config.toml` to set model path:

```toml
[server]
host = "0.0.0.0"
port = 8766

[model]
path = "../models/ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf"  # Change to your model path
name = "ernie-21b"

[inference]
n_ctx = 16384        # Maximum context length
n_threads = 10       # CPU threads (recommended: number of physical cores)
n_gpu_layers = 0     # Set to 0 for pure CPU inference
use_mmap = true      # Use memory mapping to reduce RAM usage
n_batch = 512        # Batch size

[embedding]
model_path = "../models/bge-m3-Q4_K_M.gguf"  # Embedding model path
model_name = "bge-m3"
dimension = 1024
n_ctx = 8192
n_threads = 4
```

### 4. Build and Run

#### Windows:
```bash
# Build (only needed first time)
build.bat

# Start service
start.bat
```

> 💡 **After compilation, only 2 files needed**:
> - `llama_ernie_server.exe` (only ~5MB)
> - `config.toml` (configuration file)
> 
> You can copy these two files to any directory and run without installing any dependencies!

#### Linux / macOS:
```bash
# Build (only needed first time)
cargo build --release

# Start service
./target/release/llama_ernie_server
```

> 💡 The compiled executable is located at `target/release/llama_ernie_server`, only ~5MB

### 5. Test Service

```bash
# Health check
curl http://localhost:8766/health

# List models
curl http://localhost:8766/v1/models

# Chat test
curl http://localhost:8766/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

Or run the provided test script:

```bash
python test_openai_api.py
```

---

## 💻 API Usage Examples

### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8766/v1",
    api_key="dummy"  # Local service doesn't require real API key
)

# Chat completion
response = client.chat.completions.create(
    model="ernie-21b",
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant"},
        {"role": "user", "content": "What is artificial intelligence?"}
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
      {"role": "system", "content": "You are a professional technical consultant"},
      {"role": "user", "content": "Explain the Transformer architecture"}
    ],
    "temperature": 0.3,
    "max_tokens": 1000
  }'
```

### Embedding Vectorization

```bash
curl http://localhost:8766/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a text that needs to be vectorized"
  }'
```

```python
# Python example
import requests

response = requests.post(
    "http://localhost:8766/v1/embeddings",
    json={"text": "This is a text that needs to be vectorized"}
)

embedding = response.json()["embedding"]
print(f"Vector dimension: {len(embedding)}")
```

---

## 🔧 Advanced Configuration

### Performance Optimization Tips

#### CPU Thread Tuning
```toml
[inference]
n_threads = 10  # Set to number of physical cores (not hyperthreading count)
```

- **8-core 16-thread**: Set to 8-12
- **16-core 32-thread**: Set to 16-20
- Too many threads cause context switching overhead and reduce speed

#### Memory Optimization
```toml
[inference]
use_mmap = true    # Enable memory mapping, reduce 50%+ RAM usage
n_ctx = 16384      # Adjust based on actual needs (larger context requires more memory)
```

#### Model Quantization Options

| Quantization | RAM (21B) | Speed   | Accuracy Loss |
|--------------|-----------|---------|---------------|
| Q3_K_S       | ~8GB      | Fastest | Higher        |
| Q4_K_M       | ~12GB     | Fast    | Medium        |
| Q5_K_M       | ~15GB     | Medium  | Lower         |
| Q8_0         | ~24GB     | Slow    | Minimal       |

---

## 📊 Performance

### Test Environment
- CPU: Intel i7-12700K (12-core 20-thread)
- RAM: 32GB DDR4
- Model: ERNIE-4.5-21B-Q3_K_S
- Config: n_threads=10, n_ctx=16384

### Test Results
| Scenario                      | Time   | Speed    |
|-------------------------------|--------|----------|
| Simple QA (50 tokens)         | 3.2s   | 15.6 t/s |
| Medium response (200 tokens)  | 12.5s  | 16.0 t/s |
| Long generation (500 tokens)  | 31.2s  | 16.0 t/s |

> 💡 Speed varies based on CPU performance, model quantization level, context length, etc.

---

## 🛣️ Roadmap

- [x] **v0.1**: Basic ERNIE 4.5 inference support
- [x] **v0.2**: Full OpenAI API compatibility
- [x] **v0.3**: Embedding model integration
- [ ] **v0.4**: Streaming output (SSE) support
- [ ] **v0.5**: Multi-model management and switching
- [ ] **v0.6**: ERNIE 4.5 fine-tuned model to GGUF conversion toolkit
- [ ] **v0.7**: Batch inference optimization
- [ ] **v0.8**: GPU acceleration support (CUDA/ROCm)
- [ ] **v0.9**: Function Calling support
- [ ] **v1.0**: Production-ready stable version

---

## 🤝 Contributing

All forms of contribution are welcome!

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Plans

We are developing the following features, and contributions are welcome:

- **ERNIE Fine-tuned Model Conversion Tool**: Convert PaddlePaddle fine-tuned ERNIE models to GGUF format
- **Model Quantization Tool**: Automated ERNIE model quantization workflow
- **Performance Benchmarking**: Establish comprehensive performance test suite

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

### Dependencies

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - MIT License
- [llama-cpp-rs](https://github.com/utilityai/llama-cpp-rs) - MIT License

---

## 🙏 Acknowledgments

- Thanks to [ggerganov](https://github.com/ggerganov) for developing [llama.cpp](https://github.com/ggerganov/llama.cpp)
- Thanks to [utilityai](https://github.com/utilityai) for providing [llama-cpp-rs](https://github.com/utilityai/llama-cpp-rs) Rust bindings
- Thanks to Baidu PaddlePaddle team for developing the ERNIE model series

---

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/llama_ernie/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/llama_ernie/discussions)

---

## ⚠️ Disclaimer

This project is for learning and research purposes only. When using ERNIE models, please comply with Baidu PaddlePaddle's usage agreement and relevant laws and regulations.

---

<div align="center">

**If this project helps you, please give it a ⭐️ Star!**

Made with ❤️ by [Your Name]

</div>

