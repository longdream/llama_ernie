#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 llama_qwen.exe 服务的性能
"""

import time
import requests
import json

def test_qwen_speed(prompt: str = "用Python写一个快速排序算法", max_tokens: int = 512):
    """测试 Qwen3 服务性能"""
    
    print("=" * 70)
    print("🚀 llama_qwen.exe 性能测试")
    print("=" * 70)
    print(f"📝 Prompt: {prompt}")
    print(f"🔢 Max tokens: {max_tokens}")
    print("-" * 70)
    
    # 发送请求
    start_time = time.time()
    
    try:
        resp = requests.post(
            "http://localhost:8766/v1/chat/completions",
            json={
                "model": "qwen3-30b",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=600
        )
        
        elapsed = time.time() - start_time
        
        if resp.status_code != 200:
            print(f"❌ 请求失败: {resp.status_code}")
            print(resp.text)
            return None
        
        data = resp.json()
        
        # 提取统计信息
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # 计算速度
        tokens_per_sec = completion_tokens / elapsed if elapsed > 0 else 0
        
        # 提取输出
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        print("🤖 输出:")
        print("-" * 70)
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 70)
        print(f"📊 性能统计:")
        print(f"   - Prompt tokens: {prompt_tokens}")
        print(f"   - Completion tokens: {completion_tokens}")
        print(f"   - Total tokens: {total_tokens}")
        print(f"   - 总耗时: {elapsed:.2f}s")
        print(f"   - 生成速度: {tokens_per_sec:.2f} tokens/s")
        print("=" * 70)
        
        # 与 Ollama 对比
        ollama_speed = 11.19
        print("\n📊 与 Ollama 对比:")
        print("-" * 70)
        print(f"   Ollama qwen3:30b-a3b (GPU):     {ollama_speed:.2f} tokens/s")
        print(f"   llama_qwen.exe (CPU):          {tokens_per_sec:.2f} tokens/s")
        if tokens_per_sec > ollama_speed:
            speedup = tokens_per_sec / ollama_speed
            print(f"   🚀 llama_qwen.exe 快了约 {speedup:.1f}x !")
        elif tokens_per_sec < ollama_speed:
            ratio = ollama_speed / tokens_per_sec
            print(f"   📉 llama_qwen.exe 慢了约 {ratio:.1f}x (CPU vs GPU)")
        print("=" * 70)
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "elapsed": elapsed,
            "tokens_per_sec": tokens_per_sec,
            "content": content
        }
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保 llama_qwen.exe 正在运行")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, default="用Python写一个快速排序算法")
    parser.add_argument("--max-tokens", type=int, default=512)
    args = parser.parse_args()
    
    test_qwen_speed(args.prompt, args.max_tokens)

