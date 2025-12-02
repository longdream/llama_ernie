#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama OpenAI 兼容接口性能测试脚本
针对 qwen3:30b-a3b 模型进行多方位速度测试

测试项目:
1. 首次响应时间 (TTFT - Time To First Token)
2. 流式生成速度 (tokens/s)
3. 非流式请求总耗时
4. 不同输入长度的性能差异
5. 不同输出长度的性能差异
6. 并发请求性能
"""

import time
import json
import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, List
import statistics

# ============== 配置 ==============
OLLAMA_BASE_URL = "http://localhost:11434"
OPENAI_COMPATIBLE_URL = f"{OLLAMA_BASE_URL}/v1"
MODEL_NAME = "qwen3:30b-a3b"

# ============== 数据类 ==============
@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    ttft: float  # Time To First Token (秒)
    total_time: float  # 总耗时 (秒)
    prompt_tokens: int
    completion_tokens: int
    tokens_per_second: float
    success: bool
    error_message: Optional[str] = None

# ============== 工具函数 ==============
def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(result: TestResult):
    """打印单个测试结果"""
    if result.success:
        print(f"  ✓ {result.test_name}")
        print(f"    - 首次响应时间 (TTFT): {result.ttft:.3f}s")
        print(f"    - 总耗时: {result.total_time:.3f}s")
        print(f"    - Prompt Tokens: {result.prompt_tokens}")
        print(f"    - Completion Tokens: {result.completion_tokens}")
        print(f"    - 生成速度: {result.tokens_per_second:.2f} tokens/s")
    else:
        print(f"  ✗ {result.test_name} - 失败")
        print(f"    - 错误: {result.error_message}")

# ============== 测试函数 ==============

def test_streaming_chat(prompt: str, max_tokens: int = 200, test_name: str = "流式测试", no_think: bool = True) -> TestResult:
    """
    测试流式聊天接口 (OpenAI 兼容)
    Qwen3 模型默认启用思考模式，使用 /no_think 指令关闭
    """
    url = f"{OPENAI_COMPATIBLE_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 对 Qwen3 模型添加 /no_think 指令关闭思考模式
    actual_prompt = f"/no_think {prompt}" if no_think else prompt
    
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": actual_prompt}],
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        start_time = time.perf_counter()
        ttft = 0
        completion_tokens = 0
        reasoning_tokens = 0
        first_token_received = False
        full_content = ""
        prompt_tokens_final = 0
        completion_tokens_final = 0
        
        with requests.post(url, json=data, headers=headers, stream=True, timeout=180) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        json_str = line_str[6:]
                        if json_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(json_str)
                            
                            # 统计 token 数量
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                reasoning = delta.get("reasoning", "")  # Qwen3 思考内容
                                
                                # 记录首次响应时间 (content 或 reasoning 都算)
                                if not first_token_received and (content or reasoning):
                                    ttft = time.perf_counter() - start_time
                                    first_token_received = True
                                
                                if content:
                                    full_content += content
                                    completion_tokens += 1
                                if reasoning:
                                    reasoning_tokens += 1
                            
                            # 获取最终的 usage 信息 (如果有)
                            if "usage" in chunk:
                                prompt_tokens_final = chunk["usage"].get("prompt_tokens", 0)
                                completion_tokens_final = chunk["usage"].get("completion_tokens", 0)
                                    
                        except json.JSONDecodeError:
                            continue
        
        total_time = time.perf_counter() - start_time
        
        # 使用最终的 token 统计，如果没有则使用计数
        # 总 token = content tokens + reasoning tokens
        total_output_tokens = completion_tokens + reasoning_tokens
        if completion_tokens_final > 0:
            total_output_tokens = completion_tokens_final
        
        # 计算生成速度 (排除首次响应时间)
        generation_time = total_time - ttft if ttft > 0 else total_time
        tokens_per_second = total_output_tokens / generation_time if generation_time > 0 else 0
        
        # 估算 prompt tokens (简单按字符数估算，如果没有获取到)
        prompt_tokens = prompt_tokens_final if prompt_tokens_final > 0 else len(prompt) // 2
        
        return TestResult(
            test_name=test_name,
            ttft=ttft,
            total_time=total_time,
            prompt_tokens=prompt_tokens,
            completion_tokens=total_output_tokens,
            tokens_per_second=tokens_per_second,
            success=True
        )
        
    except Exception as e:
        return TestResult(
            test_name=test_name,
            ttft=0,
            total_time=0,
            prompt_tokens=0,
            completion_tokens=0,
            tokens_per_second=0,
            success=False,
            error_message=str(e)
        )


def test_non_streaming_chat(prompt: str, max_tokens: int = 200, test_name: str = "非流式测试", no_think: bool = True) -> TestResult:
    """
    测试非流式聊天接口 (OpenAI 兼容)
    """
    url = f"{OPENAI_COMPATIBLE_URL}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    # 对 Qwen3 模型添加 /no_think 指令关闭思考模式
    actual_prompt = f"/no_think {prompt}" if no_think else prompt
    
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": actual_prompt}],
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        start_time = time.perf_counter()
        
        response = requests.post(url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        
        total_time = time.perf_counter() - start_time
        result = response.json()
        
        # 获取 token 统计
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # 计算生成速度
        tokens_per_second = completion_tokens / total_time if total_time > 0 else 0
        
        return TestResult(
            test_name=test_name,
            ttft=total_time,  # 非流式模式下 TTFT 等于总耗时
            total_time=total_time,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens_per_second=tokens_per_second,
            success=True
        )
        
    except Exception as e:
        return TestResult(
            test_name=test_name,
            ttft=0,
            total_time=0,
            prompt_tokens=0,
            completion_tokens=0,
            tokens_per_second=0,
            success=False,
            error_message=str(e)
        )


def test_ollama_native_api(prompt: str, max_tokens: int = 200, test_name: str = "Ollama原生API测试", no_think: bool = True) -> TestResult:
    """
    测试 Ollama 原生 /api/chat 接口 (流式)
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    headers = {"Content-Type": "application/json"}
    
    # 对 Qwen3 模型添加 /no_think 指令关闭思考模式
    actual_prompt = f"/no_think {prompt}" if no_think else prompt
    
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": actual_prompt}],
        "stream": True,
        "options": {
            "num_predict": max_tokens
        }
    }
    
    try:
        start_time = time.perf_counter()
        ttft = 0
        completion_tokens = 0
        first_token_received = False
        prompt_eval_count = 0
        eval_count = 0
        eval_duration = 0
        
        with requests.post(url, json=data, headers=headers, stream=True, timeout=180) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        
                        # 记录首次响应时间
                        content = chunk.get("message", {}).get("content", "")
                        if not first_token_received and content:
                            ttft = time.perf_counter() - start_time
                            first_token_received = True
                        
                        # 统计 token 数量
                        if content:
                            completion_tokens += 1
                        
                        # 获取最终统计
                        if chunk.get("done"):
                            prompt_eval_count = chunk.get("prompt_eval_count", 0)
                            eval_count = chunk.get("eval_count", completion_tokens)
                            eval_duration = chunk.get("eval_duration", 0)  # 纳秒
                            
                    except json.JSONDecodeError:
                        continue
        
        total_time = time.perf_counter() - start_time
        
        # 使用 Ollama 返回的精确统计计算速度
        if eval_duration > 0 and eval_count > 0:
            # eval_duration 是纳秒，转换为秒
            tokens_per_second = eval_count / (eval_duration / 1e9)
        else:
            # 回退到计算方式
            generation_time = total_time - ttft if ttft > 0 else total_time
            tokens_per_second = eval_count / generation_time if generation_time > 0 else 0
        
        return TestResult(
            test_name=test_name,
            ttft=ttft,
            total_time=total_time,
            prompt_tokens=prompt_eval_count,
            completion_tokens=eval_count,
            tokens_per_second=tokens_per_second,
            success=True
        )
        
    except Exception as e:
        return TestResult(
            test_name=test_name,
            ttft=0,
            total_time=0,
            prompt_tokens=0,
            completion_tokens=0,
            tokens_per_second=0,
            success=False,
            error_message=str(e)
        )


async def test_concurrent_requests(prompts: List[str], max_tokens: int = 100, no_think: bool = True) -> List[TestResult]:
    """
    测试并发请求性能
    """
    url = f"{OPENAI_COMPATIBLE_URL}/chat/completions"
    
    async def single_request(session: aiohttp.ClientSession, prompt: str, idx: int) -> TestResult:
        # 对 Qwen3 模型添加 /no_think 指令关闭思考模式
        actual_prompt = f"/no_think {prompt}" if no_think else prompt
        
        data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": actual_prompt}],
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            start_time = time.perf_counter()
            
            async with session.post(url, json=data) as response:
                result = await response.json()
                total_time = time.perf_counter() - start_time
                
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                tokens_per_second = completion_tokens / total_time if total_time > 0 else 0
                
                return TestResult(
                    test_name=f"并发请求 #{idx+1}",
                    ttft=total_time,
                    total_time=total_time,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    tokens_per_second=tokens_per_second,
                    success=True
                )
                
        except Exception as e:
            return TestResult(
                test_name=f"并发请求 #{idx+1}",
                ttft=0,
                total_time=0,
                prompt_tokens=0,
                completion_tokens=0,
                tokens_per_second=0,
                success=False,
                error_message=str(e)
            )
    
    async with aiohttp.ClientSession() as session:
        tasks = [single_request(session, prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        return results


def check_server_status() -> bool:
    """检查 Ollama 服务状态"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_model_loaded() -> bool:
    """检查模型是否已加载"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/ps", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            for model in models:
                if MODEL_NAME in model.get("name", ""):
                    return True
        return False
    except:
        return False


def warmup_model():
    """预热模型"""
    print("\n正在预热模型...")
    url = f"{OLLAMA_BASE_URL}/api/generate"
    data = {
        "model": MODEL_NAME,
        "prompt": "hello",
        "stream": False,
        "keep_alive": "5m"
    }
    try:
        response = requests.post(url, json=data, timeout=120)
        if response.status_code == 200:
            print("✓ 模型预热完成")
            return True
        else:
            print(f"✗ 模型预热失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 模型预热失败: {e}")
        return False


# ============== 主测试流程 ==============

def run_all_tests():
    """运行所有测试"""
    
    print_header("Ollama OpenAI 兼容接口性能测试")
    print(f"模型: {MODEL_NAME}")
    print(f"服务地址: {OLLAMA_BASE_URL}")
    
    # 检查服务状态
    print("\n检查服务状态...")
    if not check_server_status():
        print("✗ Ollama 服务未运行，请先启动 Ollama")
        return
    print("✓ Ollama 服务运行中")
    
    # 预热模型
    warmup_model()
    
    all_results = []
    
    # ========== 测试 1: 基础流式测试 ==========
    print_header("测试 1: 基础流式测试 (OpenAI 兼容接口)")
    
    basic_prompts = [
        ("短提示词", "你好", 50),
        ("中等提示词", "请用简洁的语言解释什么是人工智能？", 150),
        ("长提示词", "请详细解释机器学习和深度学习的区别，包括它们的应用场景、优缺点，以及在实际项目中如何选择使用哪种技术。", 300),
    ]
    
    for name, prompt, max_tokens in basic_prompts:
        result = test_streaming_chat(prompt, max_tokens, f"流式-{name}")
        print_result(result)
        all_results.append(result)
        time.sleep(1)
    
    # ========== 测试 2: 非流式测试 ==========
    print_header("测试 2: 非流式测试 (OpenAI 兼容接口)")
    
    for name, prompt, max_tokens in basic_prompts:
        result = test_non_streaming_chat(prompt, max_tokens, f"非流式-{name}")
        print_result(result)
        all_results.append(result)
        time.sleep(1)
    
    # ========== 测试 3: Ollama 原生 API 测试 ==========
    print_header("测试 3: Ollama 原生 API 测试 (/api/chat)")
    
    for name, prompt, max_tokens in basic_prompts:
        result = test_ollama_native_api(prompt, max_tokens, f"原生API-{name}")
        print_result(result)
        all_results.append(result)
        time.sleep(1)
    
    # ========== 测试 4: 不同输出长度测试 ==========
    print_header("测试 4: 不同输出长度测试")
    
    output_length_tests = [
        ("50 tokens", 50),
        ("100 tokens", 100),
        ("200 tokens", 200),
        ("500 tokens", 500),
    ]
    
    test_prompt = "请写一篇关于人工智能发展历史的文章。"
    
    for name, max_tokens in output_length_tests:
        result = test_streaming_chat(test_prompt, max_tokens, f"输出长度-{name}")
        print_result(result)
        all_results.append(result)
        time.sleep(1)
    
    # ========== 测试 5: 代码生成测试 ==========
    print_header("测试 5: 代码生成测试")
    
    code_prompts = [
        ("简单函数", "用 Python 写一个计算斐波那契数列的函数", 200),
        ("复杂算法", "用 Python 实现一个完整的快速排序算法，包含详细注释", 400),
        ("完整程序", "用 Python 写一个简单的 HTTP 服务器，可以处理 GET 和 POST 请求", 600),
    ]
    
    for name, prompt, max_tokens in code_prompts:
        result = test_streaming_chat(prompt, max_tokens, f"代码生成-{name}")
        print_result(result)
        all_results.append(result)
        time.sleep(1)
    
    # ========== 测试 6: 并发请求测试 ==========
    print_header("测试 6: 并发请求测试")
    
    concurrent_prompts = [
        "什么是量子计算？",
        "解释一下区块链技术",
        "人工智能的未来发展趋势是什么？",
    ]
    
    print(f"  发送 {len(concurrent_prompts)} 个并发请求...")
    start_time = time.perf_counter()
    concurrent_results = asyncio.run(test_concurrent_requests(concurrent_prompts, 100))
    total_concurrent_time = time.perf_counter() - start_time
    
    for result in concurrent_results:
        print_result(result)
        all_results.append(result)
    
    print(f"\n  并发总耗时: {total_concurrent_time:.3f}s")
    
    # ========== 测试 7: 重复测试取平均值 ==========
    print_header("测试 7: 稳定性测试 (5次重复)")
    
    stability_prompt = "请简单介绍一下 Python 编程语言的特点。"
    stability_results = []
    
    for i in range(5):
        result = test_streaming_chat(stability_prompt, 150, f"稳定性测试 #{i+1}")
        print_result(result)
        if result.success:
            stability_results.append(result)
        time.sleep(2)
    
    if len(stability_results) >= 2:
        avg_ttft = statistics.mean([r.ttft for r in stability_results])
        avg_tps = statistics.mean([r.tokens_per_second for r in stability_results])
        std_tps = statistics.stdev([r.tokens_per_second for r in stability_results])
        
        print(f"\n  统计结果:")
        print(f"    - 平均 TTFT: {avg_ttft:.3f}s")
        print(f"    - 平均生成速度: {avg_tps:.2f} tokens/s")
        print(f"    - 速度标准差: {std_tps:.2f} tokens/s")
    
    # ========== 汇总报告 ==========
    print_header("性能测试汇总报告")
    
    successful_results = [r for r in all_results if r.success]
    
    if successful_results:
        print(f"\n  成功测试数: {len(successful_results)} / {len(all_results)}")
        
        # 按测试类型分组统计
        streaming_results = [r for r in successful_results if "流式" in r.test_name]
        non_streaming_results = [r for r in successful_results if "非流式" in r.test_name]
        native_results = [r for r in successful_results if "原生API" in r.test_name]
        code_results = [r for r in successful_results if "代码生成" in r.test_name]
        
        if streaming_results:
            avg_tps = statistics.mean([r.tokens_per_second for r in streaming_results])
            avg_ttft = statistics.mean([r.ttft for r in streaming_results])
            print(f"\n  流式测试 (OpenAI 兼容):")
            print(f"    - 平均 TTFT: {avg_ttft:.3f}s")
            print(f"    - 平均生成速度: {avg_tps:.2f} tokens/s")
        
        if non_streaming_results:
            avg_tps = statistics.mean([r.tokens_per_second for r in non_streaming_results])
            avg_time = statistics.mean([r.total_time for r in non_streaming_results])
            print(f"\n  非流式测试 (OpenAI 兼容):")
            print(f"    - 平均响应时间: {avg_time:.3f}s")
            print(f"    - 平均生成速度: {avg_tps:.2f} tokens/s")
        
        if native_results:
            avg_tps = statistics.mean([r.tokens_per_second for r in native_results])
            avg_ttft = statistics.mean([r.ttft for r in native_results])
            print(f"\n  Ollama 原生 API:")
            print(f"    - 平均 TTFT: {avg_ttft:.3f}s")
            print(f"    - 平均生成速度: {avg_tps:.2f} tokens/s")
        
        if code_results:
            avg_tps = statistics.mean([r.tokens_per_second for r in code_results])
            print(f"\n  代码生成测试:")
            print(f"    - 平均生成速度: {avg_tps:.2f} tokens/s")
        
        # 总体统计
        all_tps = [r.tokens_per_second for r in successful_results if r.tokens_per_second > 0]
        if all_tps:
            print(f"\n  总体统计:")
            print(f"    - 最高速度: {max(all_tps):.2f} tokens/s")
            print(f"    - 最低速度: {min(all_tps):.2f} tokens/s")
            print(f"    - 平均速度: {statistics.mean(all_tps):.2f} tokens/s")
    
    print("\n" + "=" * 60)
    print("  测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

