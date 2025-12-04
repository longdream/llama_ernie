#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载并转换 Qwen3-30B-A3B 模型为 OpenVINO 格式

由于没有预转换的模型，需要使用 optimum-intel 进行转换
"""

import os
import sys
import subprocess

def convert_qwen3_30b_a3b():
    """使用 optimum-cli 将 Qwen3-30B-A3B 转换为 OpenVINO 格式"""
    
    print("=" * 70)
    print("🚀 Qwen3-30B-A3B 模型 OpenVINO 格式转换工具")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), "Qwen3-30B-A3B-int4-ov")
    
    print(f"📦 源模型: Qwen/Qwen3-30B-A3B")
    print(f"📁 输出目录: {output_dir}")
    print(f"🔧 量化格式: int4 (GPU 优化)")
    print("-" * 70)
    print("⚠️  注意: 转换需要约 40GB+ 内存，可能需要较长时间")
    print("-" * 70)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "optimum.exporters.openvino",
        "--model", "Qwen/Qwen3-30B-A3B",
        "--task", "text-generation-with-past",
        "--weight-format", "int4",
        "--sym",
        "--group-size", "128",
        "--trust-remote-code",
        output_dir
    ]
    
    print("⏳ 开始转换，这可能需要 30-60 分钟...")
    print(f"📝 命令: {' '.join(cmd)}")
    print("-" * 70)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("-" * 70)
        print(f"✅ 模型转换完成!")
        print(f"📁 输出路径: {output_dir}")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ 转换失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


if __name__ == "__main__":
    convert_qwen3_30b_a3b()

