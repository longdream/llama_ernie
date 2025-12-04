#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenVINO GenAI 多次测试性能基准（去掉预热）

测量 Qwen3-8B-int4-ov 模型的推理速度 (tokens/s)
- 先进行预热运行，然后进行正式测试
- 统计多次运行的平均值、最小值、最大值
"""

import os
import sys
import time
import argparse
import statistics

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")


def run_benchmark(model_path: str, device: str = "CPU", max_new_tokens: int = 128, 
                  warmup_runs: int = 2, test_runs: int = 5):
    """
    运行性能基准测试（带预热）
    
    Args:
        model_path: 模型路径
        device: 运行设备 (CPU, GPU, NPU)
        max_new_tokens: 最大生成 token 数
        warmup_runs: 预热运行次数
        test_runs: 正式测试运行次数
    """
    import openvino_genai as ov_genai
    
    print("=" * 70)
    print(f"🚀 OpenVINO GenAI 性能基准测试 - {device}")
    print("=" * 70)
    print(f"📦 OpenVINO GenAI 版本: {ov_genai.__version__}")
    print(f"📁 模型路径: {model_path}")
    print(f"💻 运行设备: {device}")
    print(f"🔢 最大生成 tokens: {max_new_tokens}")
    print(f"🔥 预热轮数: {warmup_runs}")
    print(f"📊 测试轮数: {test_runs}")
    print("-" * 70)
    
    # 加载模型
    print("⏳ 正在加载模型...")
    load_start = time.time()
    pipe = ov_genai.LLMPipeline(model_path, device)
    load_time = time.time() - load_start
    print(f"✅ 模型加载完成，耗时: {load_time:.2f}s")
    print("-" * 70)
    
    prompt = "什么是人工智能？请简单解释。"
    
    def run_single_test():
        """运行单次测试，返回 (token_count, time, tokens_per_sec)"""
        token_count = 0
        
        def count_tokens(subword):
            nonlocal token_count
            token_count += 1
            return ov_genai.StreamingStatus.RUNNING
        
        start_time = time.time()
        pipe.generate(prompt, streamer=count_tokens, max_new_tokens=max_new_tokens)
        gen_time = time.time() - start_time
        
        tokens_per_sec = token_count / gen_time if gen_time > 0 else 0
        return token_count, gen_time, tokens_per_sec
    
    # 预热运行
    print(f"🔥 预热阶段 ({warmup_runs} 次)...")
    for i in range(warmup_runs):
        tokens, gen_time, tps = run_single_test()
        print(f"   预热 {i+1}: {tokens} tokens, {gen_time:.2f}s, {tps:.2f} t/s (不计入统计)")
    
    print("-" * 70)
    
    # 正式测试
    print(f"📊 正式测试阶段 ({test_runs} 次)...")
    results = []
    
    for i in range(test_runs):
        tokens, gen_time, tps = run_single_test()
        results.append({
            "tokens": tokens,
            "time": gen_time,
            "tokens_per_sec": tps
        })
        print(f"   测试 {i+1}: {tokens} tokens, {gen_time:.2f}s, {tps:.2f} t/s")
    
    # 统计结果
    tps_list = [r["tokens_per_sec"] for r in results]
    time_list = [r["time"] for r in results]
    tokens_list = [r["tokens"] for r in results]
    
    avg_tps = statistics.mean(tps_list)
    min_tps = min(tps_list)
    max_tps = max(tps_list)
    std_tps = statistics.stdev(tps_list) if len(tps_list) > 1 else 0
    
    avg_time = statistics.mean(time_list)
    avg_tokens = statistics.mean(tokens_list)
    
    print("-" * 70)
    print(f"📊 {device} 性能统计结果 (去掉预热后)")
    print("-" * 70)
    print(f"   平均生成 tokens: {avg_tokens:.0f}")
    print(f"   平均生成耗时: {avg_time:.2f}s")
    print(f"   ─────────────────────────────")
    print(f"   平均速度: {avg_tps:.2f} t/s")
    print(f"   最小速度: {min_tps:.2f} t/s")
    print(f"   最大速度: {max_tps:.2f} t/s")
    print(f"   标准差: {std_tps:.2f} t/s")
    print("=" * 70)
    
    return {
        "device": device,
        "load_time": load_time,
        "avg_tokens": avg_tokens,
        "avg_time": avg_time,
        "avg_tps": avg_tps,
        "min_tps": min_tps,
        "max_tps": max_tps,
        "std_tps": std_tps,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="OpenVINO GenAI 多次测试性能基准")
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
        default=128,
        help="最大生成 token 数 (默认: 128)"
    )
    parser.add_argument(
        "--warmup-runs",
        type=int,
        default=2,
        help="预热运行次数 (默认: 2)"
    )
    parser.add_argument(
        "--test-runs",
        type=int,
        default=5,
        help="正式测试运行次数 (默认: 5)"
    )
    parser.add_argument(
        "--all-devices",
        action="store_true",
        help="测试所有可用设备 (CPU 和 GPU)"
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
    
    if args.all_devices:
        # 测试 CPU 和 GPU
        all_results = []
        
        for device in ["CPU", "GPU"]:
            print(f"\n{'#' * 70}")
            print(f"# 测试设备: {device}")
            print(f"{'#' * 70}\n")
            
            try:
                result = run_benchmark(
                    args.model_path, 
                    device, 
                    args.max_new_tokens,
                    args.warmup_runs,
                    args.test_runs
                )
                all_results.append(result)
            except Exception as e:
                print(f"❌ {device} 测试失败: {e}")
                all_results.append({"device": device, "error": str(e)})
        
        # 汇总对比
        print("\n" + "=" * 70)
        print("📊 设备性能对比汇总")
        print("=" * 70)
        print(f"{'设备':<8} {'加载时间':<12} {'平均速度':<12} {'最小':<10} {'最大':<10} {'标准差':<10}")
        print("-" * 70)
        
        for r in all_results:
            if "error" in r:
                print(f"{r['device']:<8} {'N/A':<12} {'错误: ' + r['error'][:30]}")
            else:
                print(f"{r['device']:<8} {r['load_time']:.2f}s{'':<6} {r['avg_tps']:.2f} t/s{'':<4} {r['min_tps']:.2f}{'':<4} {r['max_tps']:.2f}{'':<4} {r['std_tps']:.2f}")
        
        print("=" * 70)
        
        # 计算性能提升
        valid_results = [r for r in all_results if "error" not in r]
        if len(valid_results) >= 2:
            cpu_result = next((r for r in valid_results if r["device"] == "CPU"), None)
            gpu_result = next((r for r in valid_results if r["device"] == "GPU"), None)
            
            if cpu_result and gpu_result:
                speedup = (gpu_result["avg_tps"] / cpu_result["avg_tps"] - 1) * 100
                print(f"\n🚀 GPU 相比 CPU 性能提升: {speedup:.1f}%")
                print(f"   CPU: {cpu_result['avg_tps']:.2f} t/s")
                print(f"   GPU: {gpu_result['avg_tps']:.2f} t/s")
    else:
        # 测试单个设备
        run_benchmark(
            args.model_path, 
            args.device, 
            args.max_new_tokens,
            args.warmup_runs,
            args.test_runs
        )


if __name__ == "__main__":
    main()





