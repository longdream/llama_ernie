#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenVINO GenAI 推理服务器 - 兼容 OpenAI API

提供与 OpenAI API 兼容的 HTTP 接口，用于 Qwen3-8B-int4-ov 模型推理

模型地址: https://www.modelscope.cn/models/OpenVINO/Qwen3-8B-int4-ov
"""

import os
import sys
import json
import time
import uuid
import argparse
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass, field

# 模型默认路径
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8767


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    messages: List[Dict[str, str]]
    model: str = "qwen3-8b-int4-ov"
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False
    top_p: float = 0.9


class OpenVINOServer:
    """OpenVINO GenAI 推理服务器"""
    
    def __init__(self, model_path: str, device: str = "CPU"):
        self.model_path = model_path
        self.device = device
        self.model_name = "qwen3-8b-int4-ov"
        self.pipe = None
        
    def load_model(self):
        """加载模型"""
        import openvino_genai as ov_genai
        
        print(f"🔧 加载模型: {self.model_path}")
        print(f"💻 运行设备: {self.device}")
        
        start_time = time.time()
        self.pipe = ov_genai.LLMPipeline(self.model_path, self.device)
        load_time = time.time() - start_time
        
        print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
        
    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        """将消息列表格式化为 prompt"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                formatted.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                formatted.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        
        # 添加助手回复的开始标记
        formatted.append("<|im_start|>assistant\n")
        
        return "\n".join(formatted)
    
    def generate(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """非流式生成"""
        import openvino_genai as ov_genai
        
        prompt = self.format_messages(request.messages)
        
        start_time = time.time()
        result = self.pipe.generate(
            prompt,
            max_new_tokens=request.max_tokens
        )
        gen_time = time.time() - start_time
        
        # 清理输出（移除结束标记）
        result = result.replace("<|im_end|>", "").strip()
        
        # 构造 OpenAI 格式响应
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(result.split()),
                "total_tokens": len(prompt.split()) + len(result.split())
            }
        }
        
        return response
    
    def generate_stream(self, request: ChatCompletionRequest) -> Generator[str, None, None]:
        """流式生成"""
        import openvino_genai as ov_genai
        
        prompt = self.format_messages(request.messages)
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        
        # 用于收集流式输出的容器
        collected_tokens = []
        
        def streamer(subword):
            # 过滤结束标记
            if "<|im_end|>" in subword:
                subword = subword.replace("<|im_end|>", "")
            if subword:
                collected_tokens.append(subword)
            return ov_genai.StreamingStatus.RUNNING
        
        # 启动生成（在后台线程中）
        import threading
        import queue
        
        token_queue = queue.Queue()
        generation_done = threading.Event()
        
        def generate_thread():
            def stream_callback(subword):
                if "<|im_end|>" in subword:
                    subword = subword.replace("<|im_end|>", "")
                if subword:
                    token_queue.put(subword)
                return ov_genai.StreamingStatus.RUNNING
            
            self.pipe.generate(
                prompt,
                streamer=stream_callback,
                max_new_tokens=request.max_tokens
            )
            generation_done.set()
        
        thread = threading.Thread(target=generate_thread)
        thread.start()
        
        # 流式输出
        while not generation_done.is_set() or not token_queue.empty():
            try:
                token = token_queue.get(timeout=0.1)
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": self.model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": token
                        },
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            except queue.Empty:
                continue
        
        thread.join()
        
        # 发送结束标记
        final_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self.model_name,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


def create_app(server: OpenVINOServer):
    """创建 Flask 应用"""
    from flask import Flask, request, jsonify, Response, stream_with_context
    
    app = Flask(__name__)
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "model": server.model_name})
    
    @app.route("/v1/models", methods=["GET"])
    def list_models():
        return jsonify({
            "object": "list",
            "data": [{
                "id": server.model_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "openvino"
            }]
        })
    
    @app.route("/v1/chat/completions", methods=["POST"])
    def chat_completions():
        data = request.json
        
        req = ChatCompletionRequest(
            messages=data.get("messages", []),
            model=data.get("model", server.model_name),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 512),
            stream=data.get("stream", False),
            top_p=data.get("top_p", 0.9)
        )
        
        if req.stream:
            return Response(
                stream_with_context(server.generate_stream(req)),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            return jsonify(server.generate(req))
    
    return app


def main():
    parser = argparse.ArgumentParser(
        description="OpenVINO GenAI 推理服务器 (兼容 OpenAI API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动服务器
  python server.py
  
  # 指定端口和设备
  python server.py --port 8080 --device GPU
  
  # 测试 API
  curl http://localhost:8767/v1/chat/completions \\
    -H "Content-Type: application/json" \\
    -d '{"messages": [{"role": "user", "content": "你好"}]}'
        """
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help=f"模型目录路径 (默认: {DEFAULT_MODEL_PATH})"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="CPU",
        choices=["CPU", "GPU", "NPU"],
        help="运行设备: CPU, GPU, NPU (默认: CPU)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"服务器地址 (默认: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"服务器端口 (默认: {DEFAULT_PORT})"
    )
    
    args = parser.parse_args()
    
    # 检查模型路径
    if not os.path.exists(args.model_path):
        print(f"❌ 模型路径不存在: {args.model_path}")
        print("💡 请先运行 download_model.py 下载模型:")
        print("   python download_model.py --source modelscope")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 OpenVINO GenAI 推理服务器")
    print("=" * 60)
    
    try:
        import openvino_genai
        print(f"📦 OpenVINO GenAI 版本: {openvino_genai.__version__}")
    except ImportError:
        print("❌ 请先安装 openvino-genai:")
        print("   pip install openvino-genai")
        sys.exit(1)
    
    try:
        from flask import Flask
    except ImportError:
        print("❌ 请先安装 flask:")
        print("   pip install flask")
        sys.exit(1)
    
    # 创建服务器实例
    server = OpenVINOServer(args.model_path, args.device)
    server.load_model()
    
    # 创建 Flask 应用
    app = create_app(server)
    
    print("-" * 60)
    print(f"🌐 服务地址: http://{args.host}:{args.port}")
    print(f"📖 API 端点:")
    print(f"   - GET  /health              - 健康检查")
    print(f"   - GET  /v1/models           - 模型列表")
    print(f"   - POST /v1/chat/completions - 聊天补全")
    print("-" * 60)
    
    # 启动服务器
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()

