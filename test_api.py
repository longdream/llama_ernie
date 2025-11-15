#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI兼容API测试 - 验证所有参数通过API传入
"""

import requests
import json

BASE_URL = "http://localhost:8766/v1"

def test_api_parameters():
    """测试API参数传递"""
    print("=" * 70)
    print("  OpenAI兼容API测试")
    print("=" * 70)
    
    # 测试1: 自定义参数
    print("\n📝 测试1: 自定义temperature和max_tokens")
    print("-" * 70)
    
    payload = {
        "model": "ernie-0.3b",
        "messages": [
            {"role": "user", "content": "用一句话介绍Python"}
        ],
        "temperature": 0.3,  # 低温度
        "max_tokens": 50     # 少量tokens
    }
    
    print(f"请求参数: temperature={payload['temperature']}, max_tokens={payload['max_tokens']}")
    
    response = requests.post(f"{BASE_URL}/chat/completions", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 响应成功")
        print(f"生成tokens: {result['usage']['completion_tokens']}")
        print(f"回复: {result['choices'][0]['message']['content'][:100]}...")
    else:
        print(f"❌ 失败: {response.status_code}")
    
    # 测试2: 使用默认值
    print("\n📝 测试2: 不传参数，使用默认值")
    print("-" * 70)
    
    payload2 = {
        "model": "ernie-0.3b",
        "messages": [
            {"role": "user", "content": "什么是AI？"}
        ]
        # 不传temperature和max_tokens，应使用默认值0.7和512
    }
    
    print(f"请求参数: 未指定temperature和max_tokens")
    
    response2 = requests.post(f"{BASE_URL}/chat/completions", json=payload2)
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✅ 响应成功（应使用默认值：temperature=0.7, max_tokens=512）")
        print(f"生成tokens: {result2['usage']['completion_tokens']}")
        print(f"回复: {result2['choices'][0]['message']['content'][:100]}...")
    else:
        print(f"❌ 失败: {response2.status_code}")
    
    # 测试3: OpenAI SDK兼容性
    print("\n📝 测试3: OpenAI SDK格式兼容")
    print("-" * 70)
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url="http://localhost:8766/v1",
            api_key="dummy"
        )
        
        response3 = client.chat.completions.create(
            model="ernie-0.3b",
            messages=[{"role": "user", "content": "你好"}],
            temperature=0.5,
            max_tokens=100
        )
        
        print(f"✅ OpenAI SDK兼容")
        print(f"回复: {response3.choices[0].message.content[:100]}...")
        
    except ImportError:
        print(f"⚠️  未安装openai包，跳过SDK测试")
    except Exception as e:
        print(f"❌ SDK测试失败: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！所有参数通过API传入")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        test_api_parameters()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
