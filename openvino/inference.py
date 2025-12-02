#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 OpenVINO GenAI 进行 Qwen3-8B-int4-ov 模型推理

模型地址: https://www.modelscope.cn/models/OpenVINO/Qwen3-8B-int4-ov
文档参考: https://github.com/openvinotoolkit/openvino.genai
"""

import os
import sys
import argparse
import time

# 模型默认路径
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")


def simple_generate(model_path: str, prompt: str, device: str = "CPU", max_new_tokens: int = 512):
    """
    简单文本生成（非流式）
    
    Args:
        model_path: 模型目录路径
        prompt: 输入提示词
        device: 运行设备 (CPU, GPU, NPU)
        max_new_tokens: 最大生成 token 数
    """
    import openvino_genai as ov_genai
    
    print(f"🔧 加载模型: {model_path}")
    print(f"💻 运行设备: {device}")
    print("-" * 50)
    
    # 初始化 LLM Pipeline
    start_time = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - start_time
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 50)
    
    # 生成文本
    print(f"📝 输入: {prompt}")
    print("-" * 50)
    
    start_time = time.time()
    result = pipe.generate(prompt, max_new_tokens=max_new_tokens)
    gen_time = time.time() - start_time
    
    print(f"🤖 输出:\n{result}")
    print("-" * 50)
    print(f"⏱️ 生成耗时: {gen_time:.2f}s")
    
    return result


def streaming_generate(model_path: str, prompt: str, device: str = "CPU", max_new_tokens: int = 512):
    """
    流式文本生成（实时输出）
    
    Args:
        model_path: 模型目录路径
        prompt: 输入提示词
        device: 运行设备 (CPU, GPU, NPU)
        max_new_tokens: 最大生成 token 数
    """
    import openvino_genai as ov_genai
    
    print(f"🔧 加载模型: {model_path}")
    print(f"💻 运行设备: {device}")
    print("-" * 50)
    
    # 初始化 LLM Pipeline
    start_time = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - start_time
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 50)
    
    print(f"📝 输入: {prompt}")
    print("-" * 50)
    print("🤖 输出: ", end="", flush=True)
    
    # 定义流式输出回调函数
    token_count = 0
    start_time = time.time()
    
    def streamer(subword):
        nonlocal token_count
        print(subword, end="", flush=True)
        token_count += 1
        # 返回 RUNNING 表示继续生成
        return ov_genai.StreamingStatus.RUNNING
    
    # 流式生成
    pipe.generate(prompt, streamer=streamer, max_new_tokens=max_new_tokens)
    
    gen_time = time.time() - start_time
    print("\n" + "-" * 50)
    print(f"⏱️ 生成耗时: {gen_time:.2f}s")
    if gen_time > 0:
        print(f"📊 生成速度: {token_count / gen_time:.2f} tokens/s")


def interactive_chat(model_path: str, device: str = "CPU", max_new_tokens: int = 512):
    """
    交互式对话模式
    
    Args:
        model_path: 模型目录路径
        device: 运行设备 (CPU, GPU, NPU)
        max_new_tokens: 最大生成 token 数
    """
    import openvino_genai as ov_genai
    
    print(f"🔧 加载模型: {model_path}")
    print(f"💻 运行设备: {device}")
    print("-" * 50)
    
    # 初始化 LLM Pipeline
    start_time = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - start_time
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 50)
    
    print("💬 进入交互对话模式")
    print("💡 提示: 输入 'exit' 或 'quit' 退出, 输入 'clear' 清除对话历史")
    print("=" * 50)
    
    # 定义流式输出回调函数
    def streamer(subword):
        print(subword, end="", flush=True)
        return ov_genai.StreamingStatus.RUNNING
    
    # 开始对话
    pipe.start_chat()
    
    try:
        while True:
            try:
                prompt = input("\n👤 用户: ").strip()
            except EOFError:
                break
            
            if not prompt:
                continue
            
            if prompt.lower() in ["exit", "quit", "退出"]:
                print("👋 再见!")
                break
            
            if prompt.lower() in ["clear", "清除"]:
                pipe.finish_chat()
                pipe.start_chat()
                print("🗑️ 对话历史已清除")
                continue
            
            print("\n🤖 助手: ", end="", flush=True)
            start_time = time.time()
            pipe.generate(prompt, streamer=streamer, max_new_tokens=max_new_tokens)
            gen_time = time.time() - start_time
            print(f"\n   [耗时: {gen_time:.2f}s]")
            
    except KeyboardInterrupt:
        print("\n\n👋 对话已中断")
    finally:
        pipe.finish_chat()


def main():
    parser = argparse.ArgumentParser(
        description="Qwen3-8B-int4-ov OpenVINO 推理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 简单生成
  python inference.py --prompt "什么是人工智能？"
  
  # 流式生成
  python inference.py --prompt "写一首关于春天的诗" --streaming
  
  # 交互对话
  python inference.py --chat
  
  # 使用 GPU 加速
  python inference.py --prompt "Hello" --device GPU
        """
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help=f"模型目录路径 (默认: {DEFAULT_MODEL_PATH})"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="输入提示词"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="CPU",
        choices=["CPU", "GPU", "NPU"],
        help="运行设备: CPU, GPU, NPU (默认: CPU)"
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=512,
        help="最大生成 token 数 (默认: 512)"
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="启用流式输出"
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="启用交互对话模式"
    )
    
    args = parser.parse_args()
    
    # 检查模型路径
    if not os.path.exists(args.model_path):
        print(f"❌ 模型路径不存在: {args.model_path}")
        print("💡 请先运行 download_model.py 下载模型:")
        print("   python download_model.py --source modelscope")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 Qwen3-8B-int4-ov OpenVINO 推理")
    print("=" * 60)
    
    try:
        import openvino_genai
        print(f"📦 OpenVINO GenAI 版本: {openvino_genai.__version__}")
    except ImportError:
        print("❌ 请先安装 openvino-genai:")
        print("   pip install openvino-genai")
        sys.exit(1)
    
    if args.chat:
        # 交互对话模式
        interactive_chat(args.model_path, args.device, args.max_new_tokens)
    elif args.prompt:
        # 单次生成
        if args.streaming:
            streaming_generate(args.model_path, args.prompt, args.device, args.max_new_tokens)
        else:
            simple_generate(args.model_path, args.prompt, args.device, args.max_new_tokens)
    else:
        # 默认测试
        test_prompt = "什么是 OpenVINO？请用简单的语言解释。"
        print(f"💡 未指定 prompt，使用默认测试: {test_prompt}")
        print()
        streaming_generate(args.model_path, test_prompt, args.device, args.max_new_tokens)


if __name__ == "__main__":
    main()

