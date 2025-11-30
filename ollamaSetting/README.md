# OllamaSetting - Ollama GPU 配置工具

一个基于 Tauri + Vue 3 + TypeScript 开发的 Intel Arc GPU 配置工具，用于管理 Ollama 的 GPU 设置、模型管理和性能测试。

## 功能特性

- 🔧 **GPU 配置管理**: 支持 Intel Arc GPU 的 Vulkan 配置
- 📦 **模型管理**: 下载、导入、删除、预加载模型
- ⚡ **性能测试**: HTTP 流式 API 测试，实时显示生成速度
- 🧠 **Think 模式**: 支持 Qwen3 等模型的思考过程开关
- 📊 **性能监控**: 实时统计 tokens/s、GPU 使用率等指标

---

## Ollama HTTP API 接口说明

本工具使用 Ollama 的 HTTP API 进行模型管理和推理测试。Ollama 服务默认运行在 `http://localhost:11434`。

### 基础接口地址

| 接口 | 地址 | 说明 |
|------|------|------|
| **服务地址** | `http://localhost:11434` | Ollama 默认服务地址 |
| **生成接口** | `POST /api/generate` | 文本生成（单轮对话） |
| **聊天接口** | `POST /api/chat` | 多轮对话（推荐） |
| **模型列表** | `GET /api/tags` | 获取已安装模型 |
| **拉取模型** | `POST /api/pull` | 下载模型 |
| **删除模型** | `DELETE /api/delete` | 删除模型 |

### 生成接口 `/api/generate`

用于单轮文本生成，本工具的预加载功能使用此接口。

```bash
# 非流式请求（预加载使用）
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:30b-a3b",
    "prompt": "你好",
    "stream": false,
    "keep_alive": "5m"
  }'
```

**请求参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string | 模型名称（必填） |
| `prompt` | string | 输入提示词 |
| `stream` | boolean | 是否流式输出（默认 true） |
| `keep_alive` | string | 模型保留时间：`5m`、`1h`、`24h`、`-1`(永久)、`0`(立即卸载) |

**响应字段**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `response` | string | 生成的文本 |
| `total_duration` | number | 总耗时（纳秒） |
| `load_duration` | number | 模型加载耗时（纳秒） |
| `prompt_eval_count` | number | Prompt token 数量 |
| `prompt_eval_duration` | number | Prompt 处理耗时（纳秒） |
| `eval_count` | number | 生成 token 数量 |
| `eval_duration` | number | 生成耗时（纳秒） |

### 聊天接口 `/api/chat`

用于多轮对话，本工具的性能测试使用此接口进行流式测试。

```bash
# 流式请求（性能测试使用）
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:30b-a3b",
    "messages": [
      {"role": "user", "content": "用 Python 写一个快速排序算法"}
    ],
    "stream": true
  }'
```

**请求参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string | 模型名称（必填） |
| `messages` | array | 对话消息列表 |
| `stream` | boolean | 是否流式输出（默认 true） |

**消息格式**:
```json
{
  "role": "user",      // 或 "assistant", "system"
  "content": "消息内容"
}
```

**流式响应** (每行一个 JSON):
```json
{"model":"qwen3:30b-a3b","message":{"role":"assistant","content":"好"},"done":false}
{"model":"qwen3:30b-a3b","message":{"role":"assistant","content":"的"},"done":false}
...
{"model":"qwen3:30b-a3b","done":true,"total_duration":12345678,"eval_count":100,...}
```

### Think 模式（Qwen3 等模型）

Qwen3 等模型支持思考模式，可以在 prompt 中添加指令控制：

```bash
# 关闭思考模式
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen3:30b-a3b","prompt":"/no_think 你好","stream":false}'

# 开启思考模式（默认）
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen3:30b-a3b","prompt":"你好","stream":false}'
```

本工具在「模型管理」→「预加载设置」中提供 Think 模式开关，会自动在请求中添加 `/no_think` 指令。

---

## 多模型并行运行配置

Ollama 支持同时加载多个模型到内存，通过环境变量配置：

### 环境变量配置

```bash
# 设置最大并行模型数量（默认为 1）
set OLLAMA_MAX_LOADED_MODELS=2

# 设置 GPU 显存上限（可选，单位 GB）
set OLLAMA_MAX_VRAM=12

# 启动 Ollama 服务
ollama serve
```

### Windows PowerShell 配置

```powershell
# 临时设置（当前会话有效）
$env:OLLAMA_MAX_LOADED_MODELS = "2"
ollama serve

# 永久设置（系统环境变量）
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "2", "User")
```

### Linux/macOS 配置

```bash
# 临时设置
export OLLAMA_MAX_LOADED_MODELS=2
ollama serve

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OLLAMA_MAX_LOADED_MODELS=2' >> ~/.bashrc
source ~/.bashrc
```

### systemd 服务配置 (Linux)

编辑 `/etc/systemd/system/ollama.service`:

```ini
[Service]
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_MAX_VRAM=12"
```

然后重启服务：

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 相关环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_MAX_LOADED_MODELS` | 1 | 最大同时加载的模型数量 |
| `OLLAMA_MAX_VRAM` | - | GPU 显存上限（GB） |
| `OLLAMA_NUM_PARALLEL` | 1 | 每个模型的并行请求数 |
| `OLLAMA_KEEP_ALIVE` | 5m | 默认模型保留时间 |
| `OLLAMA_HOST` | 127.0.0.1:11434 | 服务监听地址 |

### 注意事项

1. **显存限制**: 多模型并行需要足够的 GPU 显存，建议根据模型大小合理设置
2. **性能影响**: 同时加载多个模型会分摊 GPU 资源，单模型推理速度可能下降
3. **本工具默认行为**: 本工具的预加载功能会先卸载其他模型，确保单模型运行以获得最佳性能

---

## 环境要求

在编译和运行之前，请确保已安装以下环境：

- **Node.js** (v18+)
- **pnpm** (包管理器)
- **Rust** (最新稳定版)
- **Visual Studio Build Tools** (Windows 需要 C++ 编译环境)
- **Ollama** (已安装并运行)

### 安装 pnpm

```bash
npm install -g pnpm
```

### 安装 Rust

访问 https://rustup.rs/ 下载安装 Rust。

### 安装 Ollama

访问 https://ollama.com/ 下载安装 Ollama。

## 开发模式

### 1. 安装依赖

```bash
cd ollamaSetting
pnpm install
```

### 2. 启动开发服务器

```bash
pnpm tauri dev
```

这将同时启动：
- Vite 开发服务器 (http://localhost:1420)
- Tauri 桌面应用窗口

## 生产构建

### 构建安装包

```bash
pnpm tauri build
```

构建完成后，安装包将位于：

```
src-tauri/target/release/bundle/
├── msi/          # Windows MSI 安装包
└── nsis/         # Windows NSIS 安装包
```

## 项目结构

```
ollamaSetting/
├── src/                    # Vue 前端源码
│   ├── components/
│   │   ├── ModelManager.vue    # 模型管理组件
│   │   └── PerformanceMonitor.vue  # 性能测试组件
│   └── ...
├── src-tauri/              # Tauri/Rust 后端源码
│   ├── src/
│   │   ├── main.rs         # 应用入口
│   │   ├── lib.rs          # 库入口
│   │   ├── cmd.rs          # 命令模块
│   │   ├── config.rs       # 配置模块
│   │   ├── gpu.rs          # GPU 相关功能
│   │   └── ollama.rs       # Ollama 相关功能
│   ├── Cargo.toml          # Rust 依赖配置
│   └── tauri.conf.json     # Tauri 配置
├── package.json            # Node.js 依赖配置
└── vite.config.ts          # Vite 配置
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `pnpm install` | 安装前端依赖 |
| `pnpm tauri dev` | 启动开发模式 |
| `pnpm tauri build` | 构建生产版本 |
| `pnpm dev` | 仅启动前端开发服务器 |
| `pnpm build` | 仅构建前端 |

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite + Tailwind CSS + ECharts
- **后端**: Rust + Tauri 2.0
- **UI**: Tailwind CSS v4

## 使用的 Ollama API

本工具主要使用以下 Ollama HTTP API：

| 功能 | API | 说明 |
|------|-----|------|
| 模型预加载 | `POST /api/generate` | 发送简单请求触发模型加载 |
| 性能测试 | `POST /api/chat` | 流式请求测试生成速度 |
| 模型卸载 | `POST /api/generate` | 设置 `keep_alive: "0"` 卸载模型 |

命令行工具：
| 功能 | 命令 | 说明 |
|------|------|------|
| 列出模型 | `ollama list` | 获取已安装模型列表 |
| 运行状态 | `ollama ps` | 查看当前加载的模型 |
| 下载模型 | `ollama pull <model>` | 下载指定模型 |
| 删除模型 | `ollama rm <model>` | 删除指定模型 |
| 导入模型 | `ollama create <name> -f Modelfile` | 从 GGUF 导入模型 |
