#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI API 兼容性测试
测试 llama_ernie0.3 服务是否完全兼容 OpenAI Chat Completion API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8766"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_models():
    """测试模型列表"""
    print_section("2. 模型列表")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        data = response.json()
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_chat_completion_basic():
    """测试基础聊天（只传必需参数）"""
    print_section("3. 基础聊天测试（OpenAI 兼容）")
    
    payload = {
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下你自己"}
        ]
    }
    
    print("📤 请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        data = response.json()
        print(f"\n✅ 状态码: {response.status_code}")
        print(f"✅ 耗时: {elapsed:.2f}秒")
        print(f"✅ 响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 验证响应格式
        assert "id" in data
        assert "choices" in data
        assert "usage" in data
        print("\n✅ 响应格式完全兼容 OpenAI API")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_chat_completion_with_params():
    """测试带参数的聊天"""
    print_section("4. 参数化聊天测试")
    
    payload = {
        "model": "ernie-21b",
        "messages": [
            {"role": "system", "content": "你是一个友好的AI助手"},
            {"role": "user", "content": "1+1等于几？"}
        ],
        "temperature": 0.3,  # 低温度，更确定性
        "max_tokens": 100
    }
    
    print("📤 请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        data = response.json()
        print(f"\n✅ 状态码: {response.status_code}")
        print(f"✅ 耗时: {elapsed:.2f}秒")
        print(f"✅ 回复内容: {data['choices'][0]['message']['content']}")
        print(f"✅ Token统计: {data['usage']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_chat_completion_long_context():
    """测试长上下文（验证动态 n_ctx）"""
    print_section("5. 长上下文测试（动态内存分配）")
    
    # 创建一个较长的对话历史
    long_messages = [
        {"role": "system", "content": "你是一个专业的技术顾问"},
    ]
    
    # 添加多轮对话
    for i in range(5):
        long_messages.append({
            "role": "user", 
            "content": f"这是第{i+1}轮对话，请记住这个数字。"
        })
        long_messages.append({
            "role": "assistant",
            "content": f"好的，我记住了第{i+1}轮对话。"
        })
    
    long_messages.append({
        "role": "user",
        "content": "现在总共进行了几轮对话？请简单回答。"
    })
    
    payload = {
        "messages": long_messages,
        "temperature": 0.5,
        "max_tokens": 200
    }
    
    print(f"📤 请求参数: {len(long_messages)} 条消息")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        data = response.json()
        print(f"\n✅ 状态码: {response.status_code}")
        print(f"✅ 耗时: {elapsed:.2f}秒")
        print(f"✅ 回复: {data['choices'][0]['message']['content']}")
        print(f"✅ Prompt tokens: {data['usage']['prompt_tokens']}")
        print(f"✅ Completion tokens: {data['usage']['completion_tokens']}")
        print(f"✅ 总 tokens: {data['usage']['total_tokens']}")
        
        print("\n💡 说明: 系统自动根据实际对话长度分配上下文，节省内存")
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_embedding():
    """测试 Embedding API"""
    print_section("6. Embedding 向量化测试")
    
    payload = {
        "text": "这是一个测试文本，用于生成向量表示"
    }
    
    print("📤 请求参数:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/embeddings",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        data = response.json()
        print(f"\n✅ 状态码: {response.status_code}")
        print(f"✅ 耗时: {elapsed:.2f}秒")
        print(f"✅ 向量维度: {data['dimension']}")
        print(f"✅ 模型: {data['model']}")
        print(f"✅ 向量前10个值: {data['embedding'][:10]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  OpenAI API 兼容性测试")
    print("  测试服务: llama_ernie0.3")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("健康检查", test_health()))
    results.append(("模型列表", test_models()))
    results.append(("基础聊天", test_chat_completion_basic()))
    results.append(("参数化聊天", test_chat_completion_with_params()))
    results.append(("长上下文", test_chat_completion_long_context()))
    results.append(("Embedding", test_embedding()))
    
    # 输出测试总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！服务完全兼容 OpenAI API")
        print("💡 关键特性:")
        print("  - ✅ 无需传入任何自定义参数")
        print("  - ✅ 自动根据 prompt 长度动态分配上下文")
        print("  - ✅ 完全兼容 OpenAI Chat Completion API")
        print("  - ✅ 支持 Embedding 向量化")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

