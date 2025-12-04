#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 HuggingFace 下载 Qwen3-14B-int4-ov OpenVINO 模型

模型地址: https://huggingface.co/OpenVINO/Qwen3-14B-int4-ov
"""

import os
import sys

def download_qwen3_14b():
    """从 HuggingFace 下载 Qwen3-14B-int4-ov 模型"""
    try:
        from huggingface_hub import snapshot_download
        
        model_id = "OpenVINO/Qwen3-14B-int4-ov"
        model_dir = os.path.join(os.path.dirname(__file__), "Qwen3-14B-int4-ov")
        
        print("=" * 60)
        print("🚀 Qwen3-14B-int4-ov OpenVINO 模型下载工具")
        print("=" * 60)
        print(f"📦 模型 ID: {model_id}")
        print(f"📁 目标目录: {model_dir}")
        print("-" * 60)
        print("⏳ 开始下载，请稍候...")
        print("   (模型约 8GB，下载时间取决于网络速度)")
        print("-" * 60)
        
        # 下载模型
        local_path = snapshot_download(
            repo_id=model_id,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        print("-" * 60)
        print(f"✅ 模型下载完成!")
        print(f"📁 模型路径: {local_path}")
        return local_path
        
    except ImportError:
        print("❌ 请先安装 huggingface_hub: pip install huggingface_hub")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_qwen3_14b()

