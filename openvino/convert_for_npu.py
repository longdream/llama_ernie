#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 Qwen3-8B 模型转换为 NPU 可用的 OpenVINO 格式

NPU 需要特定的量化格式 (nf4 或 int4_sym) 才能正常运行
"""

import os
import sys
import subprocess

def convert_model_for_npu():
    """使用 optimum-cli 将模型转换为 NPU 格式"""
    
    print("=" * 70)
    print("🚀 Qwen3-8B 模型 NPU 格式转换工具")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), "Qwen3-8B-npu-ov")
    
    print(f"📦 源模型: Qwen/Qwen3-8B")
    print(f"📁 输出目录: {output_dir}")
    print(f"🔧 量化格式: int4_sym (NPU 优化)")
    print("-" * 70)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "optimum.exporters.openvino",
        "--model", "Qwen/Qwen3-8B",
        "--task", "text-generation-with-past",
        "--weight-format", "int4_sym",
        "--sym",
        "--group-size", "128",
        output_dir
    ]
    
    print("⏳ 开始转换，这可能需要几分钟...")
    print(f"📝 命令: {' '.join(cmd)}")
    print("-" * 70)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
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


def download_small_model_for_npu():
    """下载较小的模型用于 NPU 测试"""
    from huggingface_hub import snapshot_download
    
    # 使用较小的模型进行 NPU 测试
    model_id = "OpenVINO/Qwen3-0.6B-int4-ov"
    model_dir = os.path.join(os.path.dirname(__file__), "Qwen3-0.6B-int4-ov")
    
    print("=" * 70)
    print("🚀 下载 Qwen3-0.6B-int4-ov 模型用于 NPU 测试")
    print("=" * 70)
    print(f"📦 模型 ID: {model_id}")
    print(f"📁 目标目录: {model_dir}")
    print("-" * 70)
    
    try:
        local_path = snapshot_download(
            repo_id=model_id,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ 下载完成: {local_path}")
        return local_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NPU 模型转换/下载工具")
    parser.add_argument("--download-small", action="store_true", help="下载小模型用于 NPU 测试")
    parser.add_argument("--convert", action="store_true", help="转换 Qwen3-8B 为 NPU 格式")
    
    args = parser.parse_args()
    
    if args.download_small:
        download_small_model_for_npu()
    elif args.convert:
        convert_model_for_npu()
    else:
        print("用法:")
        print("  python convert_for_npu.py --download-small  # 下载小模型用于 NPU 测试")
        print("  python convert_for_npu.py --convert         # 转换 8B 模型为 NPU 格式")

