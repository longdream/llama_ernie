#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 optimum-intel 将 Qwen3-30B-A3B 转换为 OpenVINO 格式
"""

import os
import gc
import torch

def convert_qwen3_30b_a3b():
    """转换 Qwen3-30B-A3B 为 OpenVINO 格式"""
    from optimum.intel import OVModelForCausalLM
    from transformers import AutoTokenizer
    
    model_id = "Qwen/Qwen3-30B-A3B"
    output_dir = os.path.join(os.path.dirname(__file__), "Qwen3-30B-A3B-int4-ov")
    
    print("=" * 70)
    print("🚀 Qwen3-30B-A3B OpenVINO 转换")
    print("=" * 70)
    print(f"📦 源模型: {model_id}")
    print(f"📁 输出目录: {output_dir}")
    print("-" * 70)
    
    # 清理内存
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    print("⏳ 正在加载并转换模型 (这可能需要 30-60 分钟)...")
    print("   模型将自动下载并转换为 INT4 量化格式")
    print("-" * 70)
    
    try:
        # 加载并转换模型
        model = OVModelForCausalLM.from_pretrained(
            model_id,
            export=True,
            load_in_4bit=True,
            trust_remote_code=True,
        )
        
        # 保存模型
        print("⏳ 正在保存转换后的模型...")
        model.save_pretrained(output_dir)
        
        # 保存 tokenizer
        print("⏳ 正在保存 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        tokenizer.save_pretrained(output_dir)
        
        print("-" * 70)
        print(f"✅ 模型转换完成!")
        print(f"📁 输出路径: {output_dir}")
        
        # 清理内存
        del model
        gc.collect()
        
        return output_dir
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    convert_qwen3_30b_a3b()

