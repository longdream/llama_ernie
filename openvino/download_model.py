#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 ModelScope 下载 Qwen3-8B-int4-ov OpenVINO 模型

模型地址: https://www.modelscope.cn/models/OpenVINO/Qwen3-8B-int4-ov
"""

import os
import sys

def download_from_modelscope():
    """从 ModelScope 下载模型"""
    try:
        from modelscope import snapshot_download
        
        model_id = "OpenVINO/Qwen3-8B-int4-ov"
        model_dir = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")
        
        print(f"📦 开始从 ModelScope 下载模型: {model_id}")
        print(f"📁 目标目录: {model_dir}")
        print("-" * 50)
        
        # 下载模型
        local_path = snapshot_download(
            model_id=model_id,
            cache_dir=os.path.dirname(__file__),
            local_dir=model_dir
        )
        
        print("-" * 50)
        print(f"✅ 模型下载完成!")
        print(f"📁 模型路径: {local_path}")
        return local_path
        
    except ImportError:
        print("❌ 请先安装 modelscope: pip install modelscope")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)


def download_from_huggingface():
    """从 HuggingFace 下载模型（备用）"""
    try:
        import huggingface_hub as hf_hub
        
        model_id = "OpenVINO/Qwen3-8B-int4-ov"
        model_dir = os.path.join(os.path.dirname(__file__), "Qwen3-8B-int4-ov")
        
        print(f"📦 开始从 HuggingFace 下载模型: {model_id}")
        print(f"📁 目标目录: {model_dir}")
        print("-" * 50)
        
        # 下载模型
        local_path = hf_hub.snapshot_download(
            model_id,
            local_dir=model_dir
        )
        
        print("-" * 50)
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
    import argparse
    
    parser = argparse.ArgumentParser(description="下载 Qwen3-8B-int4-ov OpenVINO 模型")
    parser.add_argument(
        "--source", 
        type=str, 
        default="modelscope",
        choices=["modelscope", "huggingface"],
        help="下载源: modelscope (推荐国内) 或 huggingface"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Qwen3-8B-int4-ov OpenVINO 模型下载工具")
    print("=" * 60)
    
    if args.source == "modelscope":
        download_from_modelscope()
    else:
        download_from_huggingface()

