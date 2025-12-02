# OpenVINO Qwen3-8B-int4-ov 推理指南

本目录包含使用 OpenVINO GenAI 对 Qwen3-8B-int4-ov 模型进行推理的完整工具集。

## 模型信息

- **模型名称**: Qwen3-8B-int4-ov
- **模型地址**: https://www.modelscope.cn/models/OpenVINO/Qwen3-8B-int4-ov
- **量化格式**: INT4
- **推理框架**: OpenVINO GenAI

## 文件说明

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python 依赖包列表 |
| `download_model.py` | 模型下载工具 |
| `inference.py` | 推理脚本（支持简单生成、流式生成、交互对话） |
| `server.py` | HTTP API 服务器（兼容 OpenAI API） |

## 快速开始

### 1. 安装依赖

```bash
cd openvino
pip install -r requirements.txt
pip install flask  # 如果需要运行服务器
```

### 2. 下载模型

```bash
# 从 ModelScope 下载（推荐国内用户）
python download_model.py --source modelscope

# 或从 HuggingFace 下载
python download_model.py --source huggingface
```

### 3. 运行推理

#### 简单生成

```bash
python inference.py --prompt "什么是人工智能？"
```

#### 流式生成

```bash
python inference.py --prompt "写一首关于春天的诗" --streaming
```

#### 交互对话

```bash
python inference.py --chat
```

#### 使用 GPU 加速

```bash
python inference.py --prompt "Hello" --device GPU
```

### 4. 启动 API 服务器

```bash
python server.py --port 8767
```

#### 测试 API

```bash
# 健康检查
curl http://localhost:8767/health

# 聊天补全
curl http://localhost:8767/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 512
  }'
```

## 设备支持

| 设备 | 参数值 | 说明 |
|------|--------|------|
| CPU | `CPU` | 默认，兼容性最好 |
| GPU | `GPU` | Intel 集成/独立显卡 |
| NPU | `NPU` | Intel AI 加速器 |

## 环境要求

- Python 3.8+
- OpenVINO 2025.1.0+
- 内存: 建议 16GB+

## 参考链接

- [OpenVINO GenAI GitHub](https://github.com/openvinotoolkit/openvino.genai)
- [ModelScope 模型页面](https://www.modelscope.cn/models/OpenVINO/Qwen3-8B-int4-ov)
- [OpenVINO 官方文档](https://docs.openvino.ai/)

