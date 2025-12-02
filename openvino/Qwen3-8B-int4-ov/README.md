---
license: apache-2.0
license_link: https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE
base_model: 
  - Qwen/Qwen3-8B
base_model_relation: quantized

---
# Qwen3-8B-int4-ov
 * Model creator: [Qwen](https://huggingface.co/Qwen)
 * Original model: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B)

## Description
This is [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) model converted to the [OpenVINO™ IR](https://docs.openvino.ai/2025/documentation/openvino-ir-format.html) (Intermediate Representation) format with weights compressed to INT4 by [NNCF](https://github.com/openvinotoolkit/nncf).

## Quantization Parameters

The quantization was performed using `optimum-cli export openvino` with the following parameters:

 * mode: **INT4_ASYM** 
 * ratio: **1.0** 
 * group_size: **128** 
 * scale_estimation: **True** 
 * dataset: **wikitext2** 

For more information on quantization, check the [OpenVINO model optimization guide](https://docs.openvino.ai/2025/openvino-workflow/model-optimization-guide/weight-compression.html).

## Compatibility

The provided OpenVINO™ IR model is compatible with:

* OpenVINO version 2025.1.0 and higher
* Optimum Intel 1.24.0 and higher

## Running Model Inference with [Optimum Intel](https://huggingface.co/docs/optimum/intel/index)

1. Install packages required for using [Optimum Intel](https://huggingface.co/docs/optimum/intel/index) integration with the OpenVINO backend:

```
pip install optimum[openvino]
```

2. Run model inference:

```
from transformers import AutoTokenizer
from optimum.intel.openvino import OVModelForCausalLM

model_id = "OpenVINO/qwen3-8b-int4-ov"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = OVModelForCausalLM.from_pretrained(model_id)

inputs = tokenizer("What is OpenVINO?", return_tensors="pt")

outputs = model.generate(**inputs, max_length=200)
text = tokenizer.batch_decode(outputs)[0]
print(text)
```

For more examples and possible optimizations, refer to the [Inference with Optimum Intel](https://docs.openvino.ai/2025/openvino-workflow-generative/inference-with-optimum-intel.html).

## Running Model Inference with [OpenVINO GenAI](https://github.com/openvinotoolkit/openvino.genai)


1. Install packages required for using OpenVINO GenAI.
```
pip install openvino-genai huggingface_hub
```

2. Download model from HuggingFace Hub
   
```
import huggingface_hub as hf_hub

model_id = "OpenVINO/qwen3-8b-int4-ov"
model_path = "qwen3-8b-int4-ov"

hf_hub.snapshot_download(model_id, local_dir=model_path)

```

3. Run model inference:

```
import openvino_genai as ov_genai

device = "CPU"
pipe = ov_genai.LLMPipeline(model_path, device)
print(pipe.generate("What is OpenVINO?", max_length=200))
```

More GenAI usage examples can be found in OpenVINO GenAI library [docs](https://docs.openvino.ai/2025/openvino-workflow-generative/inference-with-genai.html) and [samples](https://github.com/openvinotoolkit/openvino.genai?tab=readme-ov-file#openvino-genai-samples)

You can find more detaild usage examples in OpenVINO Notebooks:

- [LLM](https://openvinotoolkit.github.io/openvino_notebooks/?search=LLM)
- [RAG text generation](https://openvinotoolkit.github.io/openvino_notebooks/?search=RAG+system&tasks=Text+Generation)

## Limitations

Check the original [model card](https://huggingface.co/Qwen/Qwen3-8B) for limitations.

## Legal information

The original model is distributed under [Apache License Version 2.0](https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE) license. More details can be found in [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B).

## Disclaimer

Intel is committed to respecting human rights and avoiding causing or contributing to adverse impacts on human rights. See [Intel’s Global Human Rights Principles](https://www.intel.com/content/dam/www/central-libraries/us/en/documents/policy-human-rights.pdf). Intel’s products and software are intended only to be used in applications that do not cause or contribute to adverse impacts on human rights.
