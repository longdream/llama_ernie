#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接使用 OpenVINO GenAI 加载 Qwen3-30B-A3B 模型进行测试
无需预先转换，OpenVINO 会自动处理
"""

import time
import sys

def test_qwen3_30b_a3b(device: str = "GPU", prompt: str = "用Python写一个快速排序算法"):
    """直接使用 OpenVINO 测试 Qwen3-30B-A3B"""
    
    try:
        import openvino_genai as ov_genai
    except ImportError:
        print("❌ 请先安装 openvino-genai: pip install openvino-genai")
        sys.exit(1)
    
    print("=" * 70)
    print("🚀 OpenVINO GenAI Qwen3-30B-A3B 直接加载测试")
    print("=" * 70)
    print(f"📦 OpenVINO GenAI 版本: {ov_genai.__version__}")
    print(f"📦 模型: Qwen/Qwen3-30B-A3B (从 HuggingFace 直接加载)")
    print(f"💻 运行设备: {device}")
    print("-" * 70)
    
    # 直接从 HuggingFace 加载模型
    print("⏳ 正在加载模型 (首次加载需要下载，请耐心等待)...")
    load_start = time.time()
    
    try:
        # 尝试直接从 HuggingFace 加载
        pipe = ov_genai.LLMPipeline("Qwen/Qwen3-30B-A3B", device)
        load_time = time.time() - load_start
        print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    except Exception as e:
        print(f"❌ 直接加载失败: {e}")
        print("\n💡 OpenVINO GenAI 需要预转换的 OpenVINO 格式模型")
        print("   HuggingFace 上没有预转换的 Qwen3-30B-A3B OpenVINO 模型")
        print("   需要使用 optimum-cli 进行转换")
        return None
    
    print("-" * 70)
    print(f"📝 输入: {prompt}")
    print("-" * 70)
    print("🤖 输出: ", end="", flush=True)
    
    # 统计
    token_count = 0
    first_token_time = None
    start_time = time.time()
    
    def streamer(subword):
        nonlocal token_count, first_token_time
        if first_token_time is None:
            first_token_time = time.time()
        print(subword, end="", flush=True)
        token_count += 1
        return ov_genai.StreamingStatus.RUNNING
    
    pipe.generate(prompt, streamer=streamer, max_new_tokens=512)
    
    gen_time = time.time() - start_time
    tokens_per_sec = token_count / gen_time if gen_time > 0 else 0
    ttft = first_token_time - start_time if first_token_time else 0
    
    print("\n" + "-" * 70)
    print(f"📊 性能统计:")
    print(f"   - 模型加载耗时: {load_time:.2f}s")
    print(f"   - 首 Token 延迟 (TTFT): {ttft:.2f}s")
    print(f"   - 生成 tokens: {token_count}")
    print(f"   - 生成耗时: {gen_time:.2f}s")
    print(f"   - 生成速度: {tokens_per_sec:.2f} tokens/s")
    print("=" * 70)
    
    # 与 Ollama 对比
    ollama_speed = 11.19
    print("\n📊 与 Ollama 对比:")
    print("-" * 70)
    print(f"   Ollama qwen3:30b-a3b (GPU):     {ollama_speed:.2f} tokens/s")
    print(f"   OpenVINO Qwen3-30B-A3B ({device}): {tokens_per_sec:.2f} tokens/s")
    if tokens_per_sec > ollama_speed:
        speedup = tokens_per_sec / ollama_speed
        print(f"   🚀 OpenVINO 快了约 {speedup:.1f}x !")
    print("=" * 70)
    
    return tokens_per_sec


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=str, default="GPU", choices=["CPU", "GPU"])
    parser.add_argument("--prompt", type=str, default="用Python写一个快速排序算法")
    args = parser.parse_args()
    
    test_qwen3_30b_a3b(args.device, args.prompt)

