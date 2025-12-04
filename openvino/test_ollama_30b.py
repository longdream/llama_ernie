#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Ollama qwen3:30b-a3b 模型性能
"""

import time
import requests
import json

def test_ollama_30b(prompt: str = "用Python写一个快速排序算法", model: str = "qwen3:30b-a3b"):
    """测试 Ollama 30B-A3B 模型性能"""
    
    print("=" * 70)
    print("🚀 Ollama qwen3:30b-a3b 性能测试")
    print("=" * 70)
    print(f"📝 模型: {model}")
    print(f"📝 Prompt: {prompt}")
    print("-" * 70)
    
    # 先检查模型是否已加载
    try:
        ps_resp = requests.get("http://localhost:11434/api/ps")
        running_models = ps_resp.json().get("models", [])
        print(f"📊 当前运行模型: {[m.get('name') for m in running_models]}")
    except:
        pass
    
    print("-" * 70)
    print("🤖 输出: ", end="", flush=True)
    
    # 发送请求
    start_time = time.time()
    first_token_time = None
    token_count = 0
    response_text = ""
    
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
            },
            stream=True,
            timeout=600
        )
        
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    token = data["response"]
                    if first_token_time is None and token:
                        first_token_time = time.time()
                    print(token, end="", flush=True)
                    response_text += token
                    token_count += 1
                
                if data.get("done"):
                    # 获取统计信息
                    total_duration = data.get("total_duration", 0) / 1e9
                    load_duration = data.get("load_duration", 0) / 1e9
                    prompt_eval_count = data.get("prompt_eval_count", 0)
                    prompt_eval_duration = data.get("prompt_eval_duration", 0) / 1e9
                    eval_count = data.get("eval_count", 0)
                    eval_duration = data.get("eval_duration", 0) / 1e9
                    
                    # 计算速率
                    prompt_eval_rate = prompt_eval_count / prompt_eval_duration if prompt_eval_duration > 0 else 0
                    eval_rate = eval_count / eval_duration if eval_duration > 0 else 0
                    
                    break
        
        gen_time = time.time() - start_time
        ttft = first_token_time - start_time if first_token_time else 0
        
        print("\n" + "-" * 70)
        print(f"📊 性能统计 (Ollama API 返回):")
        print(f"   - 总耗时: {total_duration:.2f}s")
        print(f"   - 加载耗时: {load_duration:.2f}s")
        print(f"   - Prompt 处理: {prompt_eval_count} tokens, {prompt_eval_duration:.2f}s, {prompt_eval_rate:.2f} t/s")
        print(f"   - Token 生成: {eval_count} tokens, {eval_duration:.2f}s, {eval_rate:.2f} t/s")
        print("-" * 70)
        print(f"📊 实际测量:")
        print(f"   - 首 Token 延迟 (TTFT): {ttft:.2f}s")
        print(f"   - 总生成耗时: {gen_time:.2f}s")
        print("=" * 70)
        
        return {
            "model": model,
            "prompt_eval_rate": prompt_eval_rate,
            "eval_rate": eval_rate,
            "eval_count": eval_count,
            "ttft": ttft,
            "total_time": gen_time
        }
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return None


def compare_models():
    """对比不同模型的性能"""
    prompt = "用Python写一个快速排序算法"
    
    print("\n" + "=" * 70)
    print("📊 模型性能对比")
    print("=" * 70)
    
    results = []
    
    # 测试 30b-a3b
    result = test_ollama_30b(prompt, "qwen3:30b-a3b")
    if result:
        results.append(result)
    
    # 打印对比结果
    if results:
        print("\n" + "=" * 70)
        print("📊 性能对比汇总")
        print("=" * 70)
        print(f"{'模型':<25} {'Prompt处理(t/s)':<18} {'生成速度(t/s)':<15}")
        print("-" * 70)
        for r in results:
            print(f"{r['model']:<25} {r['prompt_eval_rate']:<18.2f} {r['eval_rate']:<15.2f}")
        print("=" * 70)


if __name__ == "__main__":
    test_ollama_30b()

