#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
在 Intel Arc GPU 上测试 OpenVINO 模型性能
对比 CPU、GPU、NPU 三种设备
"""

import os
import time
import openvino_genai as ov_genai

def benchmark_on_device(model_path: str, device: str, prompt: str, max_tokens: int = 256):
    """在指定设备上进行基准测试"""
    print(f"\n{'='*60}")
    print(f"🔧 设备: {device}")
    print(f"📦 模型: {model_path}")
    print(f"{'='*60}")
    
    try:
        # 加载模型
        print(f"⏳ 正在加载模型到 {device}...")
        load_start = time.time()
        pipe = ov_genai.LLMPipeline(model_path, device)
        load_time = time.time() - load_start
        print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
        
        # 配置生成参数
        config = ov_genai.GenerationConfig()
        config.max_new_tokens = max_tokens
        config.do_sample = False  # 使用贪婪解码以便对比
        
        # 预热
        print("⏳ 预热中...")
        _ = pipe.generate("Hello", config)
        
        # 正式测试
        print(f"⏳ 开始生成 (max_tokens={max_tokens})...")
        gen_start = time.time()
        output = pipe.generate(prompt, config)
        gen_time = time.time() - gen_start
        
        # 计算 token 数（粗略估计）
        output_tokens = len(output.split())  # 粗略估计
        tokens_per_sec = max_tokens / gen_time  # 使用 max_tokens 作为上限估计
        
        print(f"\n📊 结果:")
        print(f"   生成耗时: {gen_time:.2f}s")
        print(f"   估计速度: {tokens_per_sec:.2f} tokens/s")
        print(f"\n🤖 输出预览:")
        print("-" * 40)
        print(output[:300] + ("..." if len(output) > 300 else ""))
        print("-" * 40)
        
        return {
            "device": device,
            "load_time": load_time,
            "gen_time": gen_time,
            "tokens_per_sec": tokens_per_sec,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ {device} 测试失败: {e}")
        return {
            "device": device,
            "success": False,
            "error": str(e)
        }


def main():
    # 模型路径
    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, "Qwen3-8B-int4-ov")
    
    # 测试 prompt
    prompt = "用Python写一个快速排序算法"
    max_tokens = 256
    
    print("=" * 70)
    print("🚀 Intel Core Ultra 平台 OpenVINO 性能测试")
    print("=" * 70)
    print(f"📝 Prompt: {prompt}")
    print(f"🔢 Max tokens: {max_tokens}")
    
    # 检查模型是否存在
    if not os.path.exists(model_path):
        print(f"❌ 模型不存在: {model_path}")
        return
    
    results = []
    
    # 测试不同设备
    devices = ["CPU", "GPU"]  # NPU 可能需要特殊格式的模型
    
    for device in devices:
        result = benchmark_on_device(model_path, device, prompt, max_tokens)
        results.append(result)
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 性能对比汇总")
    print("=" * 70)
    print(f"{'设备':<10} {'加载时间':<12} {'生成时间':<12} {'速度 (t/s)':<12} {'状态':<10}")
    print("-" * 70)
    
    for r in results:
        if r["success"]:
            print(f"{r['device']:<10} {r['load_time']:.2f}s{'':<6} {r['gen_time']:.2f}s{'':<6} {r['tokens_per_sec']:.2f}{'':<6} ✅")
        else:
            print(f"{r['device']:<10} {'-':<12} {'-':<12} {'-':<12} ❌ {r.get('error', '')[:30]}")
    
    print("=" * 70)
    
    # 与 llama.cpp 对比
    llama_cpp_speed = 9.45  # 之前测试的结果
    ollama_speed = 11.19
    
    print("\n📊 与其他框架对比 (Qwen3-30B-A3B):")
    print("-" * 70)
    print(f"   llama_qwen.exe (CPU):      {llama_cpp_speed:.2f} t/s")
    print(f"   Ollama (GPU):              {ollama_speed:.2f} t/s")
    
    for r in results:
        if r["success"]:
            print(f"   OpenVINO ({r['device']}):         {r['tokens_per_sec']:.2f} t/s")
    
    print("=" * 70)


if __name__ == "__main__":
    main()

