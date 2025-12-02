#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenVINO GenAI 性能基准测试

测量 Qwen3-8B-int4-ov 模型的推理速度 (tokens/s)
"""

import os
import sys
import time
import argparse

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")


def benchmark_inference(model_path: str, device: str = "CPU", max_new_tokens: int = 256, num_runs: int = 3):
    """
    运行性能基准测试
    
    Args:
        model_path: 模型路径
        device: 运行设备
        max_new_tokens: 最大生成 token 数
        num_runs: 测试运行次数
    """
    import openvino_genai as ov_genai
    
    print("=" * 70)
    print("🚀 OpenVINO GenAI 性能基准测试")
    print("=" * 70)
    print(f"📦 OpenVINO GenAI 版本: {ov_genai.__version__}")
    print(f"📁 模型路径: {model_path}")
    print(f"💻 运行设备: {device}")
    print(f"🔢 最大生成 tokens: {max_new_tokens}")
    print(f"🔄 测试轮数: {num_runs}")
    print("-" * 70)
    
    # 加载模型
    print("⏳ 正在加载模型...")
    load_start = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - load_start
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 70)
    
    # 测试用例
    test_prompts = [
        "什么是人工智能？请用简单的语言解释。",
        "请写一首关于春天的五言绝句。",
        "用 Python 写一个快速排序算法，并添加注释。",
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 测试 {i}/{len(test_prompts)}: {prompt[:30]}...")
        print("-" * 50)
        
        run_results = []
        
        for run in range(num_runs):
            # 统计生成的 token 数
            token_count = 0
            
            def count_tokens(subword):
                nonlocal token_count
                token_count += 1
                return ov_genai.StreamingStatus.RUNNING
            
            # 运行推理
            start_time = time.time()
            pipe.generate(prompt, streamer=count_tokens, max_new_tokens=max_new_tokens)
            gen_time = time.time() - start_time
            
            # 计算速度
            tokens_per_sec = token_count / gen_time if gen_time > 0 else 0
            
            run_results.append({
                "tokens": token_count,
                "time": gen_time,
                "tokens_per_sec": tokens_per_sec
            })
            
            print(f"   运行 {run + 1}: {token_count} tokens, {gen_time:.2f}s, {tokens_per_sec:.2f} t/s")
        
        # 计算平均值
        avg_tokens = sum(r["tokens"] for r in run_results) / len(run_results)
        avg_time = sum(r["time"] for r in run_results) / len(run_results)
        avg_tps = sum(r["tokens_per_sec"] for r in run_results) / len(run_results)
        
        results.append({
            "prompt": prompt[:30] + "...",
            "avg_tokens": avg_tokens,
            "avg_time": avg_time,
            "avg_tokens_per_sec": avg_tps
        })
        
        print(f"   📊 平均: {avg_tokens:.0f} tokens, {avg_time:.2f}s, {avg_tps:.2f} t/s")
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 性能测试汇总")
    print("=" * 70)
    print(f"{'测试用例':<35} {'Tokens':<10} {'耗时(s)':<10} {'速度(t/s)':<10}")
    print("-" * 70)
    
    total_tps = 0
    for r in results:
        print(f"{r['prompt']:<35} {r['avg_tokens']:<10.0f} {r['avg_time']:<10.2f} {r['avg_tokens_per_sec']:<10.2f}")
        total_tps += r["avg_tokens_per_sec"]
    
    overall_avg_tps = total_tps / len(results)
    
    print("-" * 70)
    print(f"{'总体平均速度:':<55} {overall_avg_tps:.2f} t/s")
    print("=" * 70)
    
    # 返回结果
    return {
        "model": "Qwen3-8B-int4-ov",
        "device": device,
        "load_time": load_time,
        "avg_tokens_per_sec": overall_avg_tps,
        "details": results
    }


def quick_test(model_path: str, device: str = "CPU"):
    """快速测试单次推理"""
    import openvino_genai as ov_genai
    
    print("=" * 70)
    print("🚀 OpenVINO GenAI 快速测试")
    print("=" * 70)
    print(f"📦 OpenVINO GenAI 版本: {ov_genai.__version__}")
    print(f"💻 运行设备: {device}")
    print("-" * 70)
    
    # 加载模型
    print("⏳ 正在加载模型...")
    load_start = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - load_start
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 70)
    
    prompt = "什么是 OpenVINO？请用简单的语言解释。"
    print(f"📝 输入: {prompt}")
    print("-" * 70)
    print("🤖 输出: ", end="", flush=True)
    
    # 统计
    token_count = 0
    start_time = time.time()
    
    def streamer(subword):
        nonlocal token_count
        print(subword, end="", flush=True)
        token_count += 1
        return ov_genai.StreamingStatus.RUNNING
    
    pipe.generate(prompt, streamer=streamer, max_new_tokens=256)
    
    gen_time = time.time() - start_time
    tokens_per_sec = token_count / gen_time if gen_time > 0 else 0
    
    print("\n" + "-" * 70)
    print(f"📊 性能统计:")
    print(f"   - 生成 tokens: {token_count}")
    print(f"   - 生成耗时: {gen_time:.2f}s")
    print(f"   - 生成速度: {tokens_per_sec:.2f} tokens/s")
    print("=" * 70)
    
    return tokens_per_sec


def main():
    parser = argparse.ArgumentParser(description="OpenVINO GenAI 性能基准测试")
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help=f"模型路径 (默认: {DEFAULT_MODEL_PATH})"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="CPU",
        choices=["CPU", "GPU", "NPU"],
        help="运行设备 (默认: CPU)"
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=256,
        help="最大生成 token 数 (默认: 256)"
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=3,
        help="每个测试运行次数 (默认: 3)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速测试模式（单次推理）"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.model_path):
        print(f"❌ 模型路径不存在: {args.model_path}")
        print("💡 请先运行 download_model.py 下载模型")
        sys.exit(1)
    
    try:
        import openvino_genai
    except ImportError:
        print("❌ 请先安装 openvino-genai: pip install openvino-genai")
        sys.exit(1)
    
    if args.quick:
        quick_test(args.model_path, args.device)
    else:
        benchmark_inference(args.model_path, args.device, args.max_new_tokens, args.num_runs)


if __name__ == "__main__":
    main()


