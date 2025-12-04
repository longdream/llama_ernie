<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import * as echarts from 'echarts';

interface TestResult {
  model: string;
  prompt_eval_rate: number;
  eval_rate: number;
  total_duration: string;
  load_duration: string;
  prompt_eval_count: number;
  eval_count: number;
  processor: string;
  timestamp: string;
  response: string;
}

interface Model {
  name: string;
  id: string;
  size: string;
  modified: string;
}

interface RunningModel {
  name: string;
  id: string;
  size: string;
  processor: string;
  context: string;
  until: string;
}

const loading = ref(false);
const testing = ref(false);
const models = ref<Model[]>([]);
const selectedModel = ref('');
const testPrompt = ref('用 Python 写一个快速排序算法');
const testResults = ref<TestResult[]>([]);
const currentResult = ref<TestResult | null>(null);
const chartRef = ref<HTMLDivElement | null>(null);
const logViewerRef = ref<HTMLDivElement | null>(null);

// Think 模式开关（从 localStorage 读取，与模型管理页面同步）
const enableThink = ref(localStorage.getItem('ollama_enable_think') === 'true');

// 操作日志
const logs = ref<{ type: string; message: string }[]>([]);

const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  logs.value.push({ type, message: `[${timestamp}] ${message}` });
  // 自动滚动到底部
  nextTick(() => {
    if (logViewerRef.value) {
      logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight;
    }
  });
};

let chartInstance: echarts.ECharts | null = null;

const avgEvalRate = computed(() => {
  if (testResults.value.length === 0) return 0;
  const sum = testResults.value.reduce((acc, r) => acc + r.eval_rate, 0);
  return (sum / testResults.value.length).toFixed(2);
});

const avgPromptRate = computed(() => {
  if (testResults.value.length === 0) return 0;
  const sum = testResults.value.reduce((acc, r) => acc + r.prompt_eval_rate, 0);
  return (sum / testResults.value.length).toFixed(2);
});

const gpuUsagePercent = computed(() => {
  if (testResults.value.length === 0) return 0;
  const gpuTests = testResults.value.filter(r => r.processor.includes('GPU'));
  return Math.round((gpuTests.length / testResults.value.length) * 100);
});

const loadModels = async () => {
  loading.value = true;
  addLog('info', '正在加载模型列表...');
  try {
    models.value = await invoke<Model[]>('list_ollama_models');
    if (models.value.length > 0 && !selectedModel.value) {
      selectedModel.value = models.value[0].name;
    }
    addLog('success', `成功加载 ${models.value.length} 个模型`);
  } catch (error) {
    console.error('Failed to load models:', error);
    addLog('error', `加载模型列表失败: ${error}`);
  } finally {
    loading.value = false;
  }
};

// 流式输出内容
const streamingOutput = ref('');
const thinkingOutput = ref('');

// 视觉模型图像支持
const selectedImagePath = ref('');
const selectedImageBase64 = ref('');
const imagePreviewUrl = ref('');

// 判断是否为视觉模型
const isVisionModel = computed(() => {
  const visionModels = ['qwen3-vl', 'llava', 'bakllava', 'moondream', 'llama3.2-vision', 'minicpm-v'];
  return visionModels.some(vm => selectedModel.value.toLowerCase().includes(vm));
});

// 选择图像文件
const selectImage = async () => {
  try {
    const selected = await open({
      multiple: false,
      filters: [{
        name: 'Images',
        extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp']
      }]
    });
    if (selected) {
      selectedImagePath.value = selected as string;
      // 读取图像并转换为 base64
      const imageData = await invoke<string>('read_image_base64', { imagePath: selected });
      selectedImageBase64.value = imageData;
      // 创建预览 URL
      const ext = (selected as string).split('.').pop()?.toLowerCase() || 'png';
      const mimeType = ext === 'jpg' ? 'jpeg' : ext;
      imagePreviewUrl.value = `data:image/${mimeType};base64,${imageData}`;
      addLog('success', `已选择图像: ${(selected as string).split(/[/\\]/).pop()}`);
    }
  } catch (error) {
    console.error('Failed to select image:', error);
    addLog('error', `选择图像失败: ${error}`);
  }
};

// 清除选择的图像
const clearImage = () => {
  selectedImagePath.value = '';
  selectedImageBase64.value = '';
  imagePreviewUrl.value = '';
  addLog('info', '已清除图像');
};

// 用于取消正在进行的测试
let abortController: AbortController | null = null;

const stopTest = () => {
  if (abortController) {
    abortController.abort();
    abortController = null;
    addLog('warning', '测试已取消');
  }
};

const runTest = async () => {
  if (!selectedModel.value || !testPrompt.value.trim()) {
    addLog('warning', '请选择模型并输入测试 Prompt');
    return;
  }
  
  // 如果正在测试，则取消
  if (testing.value) {
    stopTest();
    testing.value = false;
    return;
  }
  
  testing.value = true;
  currentResult.value = null;
  streamingOutput.value = '';
  thinkingOutput.value = '';
  
  // 创建新的 AbortController
  abortController = new AbortController();
  
  // 从 localStorage 重新读取 Think 设置（确保与模型管理页面同步）
  const thinkEnabled = localStorage.getItem('ollama_enable_think') === 'true';
  enableThink.value = thinkEnabled;
  
  // 获取当前运行模型的处理器信息
  let processorInfo = 'Unknown';
  try {
    const runningModels = await invoke<RunningModel[]>('get_running_models');
    const currentModel = runningModels.find(m => 
      m.name === selectedModel.value || 
      m.name === `${selectedModel.value}:latest` ||
      selectedModel.value.startsWith(m.name.split(':')[0])
    );
    if (currentModel) {
      processorInfo = currentModel.processor;
    }
  } catch (e) {
    console.log('获取处理器信息失败:', e);
  }
  
  addLog('info', '========== 开始性能测试 (HTTP 流式) ==========');
  addLog('info', `模型: ${selectedModel.value}`);
  addLog('info', `处理器: ${processorInfo}`);
  addLog('info', `显示思考过程: ${thinkEnabled ? '是' : '否'}`);
  addLog('info', `输入 Prompt: ${testPrompt.value}`);
  if (isVisionModel.value && selectedImageBase64.value) {
    addLog('info', `图像: ${selectedImagePath.value.split(/[/\\]/).pop()}`);
  }
  addLog('info', '');
  addLog('info', '>>> 开始流式输出 (点击按钮可取消) >>>');
  
  const startTime = Date.now();
  let totalTokens = 0;
  let promptTokens = 0;
  let responseText = '';
  let thinkingText = '';
  let totalDuration = 0;
  let loadDuration = 0;
  let promptEvalDuration = 0;
  let evalDuration = 0;
  
  try {
    // 构建消息内容
    let messageContent: string | Array<{ type: string; text?: string; image_url?: { url: string } }> = testPrompt.value;
    
    // 如果是视觉模型且有图像，使用多模态格式
    if (isVisionModel.value && selectedImageBase64.value) {
      messageContent = [
        { type: 'text', text: testPrompt.value },
        { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${selectedImageBase64.value}` } }
      ];
    }
    
    // 使用 HTTP 流式请求 Ollama Chat API
    const response = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: selectedModel.value,
        messages: [
          { role: 'user', content: messageContent }
        ],
        stream: true,
      }),
      signal: abortController.signal,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法获取响应流');
    }
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    // 使用异步迭代处理流，让出控制权给 UI
    const processStream = async () => {
      while (true) {
        // 检查是否被取消
        if (abortController?.signal.aborted) {
          reader.cancel();
          break;
        }
        
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // 处理可能的多行 JSON
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一个不完整的行
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const data = JSON.parse(line);
            
            // /api/chat 响应格式: { message: { role, content, thinking? }, done, ... }
            if (data.message) {
              // 提取内容
              if (data.message.content) {
                responseText += data.message.content;
                streamingOutput.value = responseText;
              }
              // 提取思考过程（如果有且用户开启了显示）
              if (data.message.thinking && thinkEnabled) {
                thinkingText += data.message.thinking;
                thinkingOutput.value = thinkingText;
              }
            }
            
            // 最后一条消息包含统计信息
            if (data.done) {
              totalDuration = data.total_duration || 0;
              loadDuration = data.load_duration || 0;
              promptEvalDuration = data.prompt_eval_duration || 0;
              evalDuration = data.eval_duration || 0;
              promptTokens = data.prompt_eval_count || 0;
              totalTokens = data.eval_count || 0;
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
        
        // 让出控制权给 UI 线程，防止卡死
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    };
    
    await processStream();
    
    // 如果被取消，不显示结果
    if (abortController?.signal.aborted) {
      return;
    }
    
    const elapsed = (Date.now() - startTime) / 1000;
    
    // 计算速率
    const promptEvalRate = promptEvalDuration > 0 
      ? promptTokens / (promptEvalDuration / 1e9) 
      : 0;
    const evalRate = evalDuration > 0 
      ? totalTokens / (evalDuration / 1e9) 
      : 0;
    
    addLog('info', '');
    addLog('info', '<<< 流式输出结束 <<<');
    addLog('info', '');
    addLog('success', `测试完成，总耗时 ${elapsed.toFixed(2)} 秒`);
    addLog('info', `生成速度: ${evalRate.toFixed(2)} tokens/s`);
    addLog('info', `Prompt 处理速度: ${promptEvalRate.toFixed(2)} tokens/s`);
    addLog('info', `Prompt Token 数: ${promptTokens}`);
    addLog('info', `生成 Token 数: ${totalTokens}`);
    addLog('info', `加载耗时: ${(loadDuration / 1e9).toFixed(2)}s`);
    addLog('info', `总耗时: ${(totalDuration / 1e9).toFixed(2)}s`);
    
    // 显示输入输出内容
    addLog('info', '');
    addLog('info', `📝 输入: ${testPrompt.value}`);
    addLog('info', `💬 输出: ${responseText.substring(0, 200)}${responseText.length > 200 ? '...' : ''}`);
    if (thinkingText && thinkEnabled) {
      addLog('info', `🧠 思考: ${thinkingText.substring(0, 100)}${thinkingText.length > 100 ? '...' : ''}`);
    }
    
    // 构建结果对象
    const result: TestResult = {
      model: selectedModel.value,
      prompt_eval_rate: promptEvalRate,
      eval_rate: evalRate,
      total_duration: `${(totalDuration / 1e9).toFixed(2)}s`,
      load_duration: `${(loadDuration / 1e9).toFixed(2)}s`,
      prompt_eval_count: promptTokens,
      eval_count: totalTokens,
      processor: processorInfo,
      timestamp: new Date().toLocaleTimeString(),
      response: responseText,
    };
    
    currentResult.value = result;
    testResults.value.unshift(result);
    
    if (testResults.value.length > 10) {
      testResults.value = testResults.value.slice(0, 10);
    }
    
    updateChart();
    addLog('success', '========== 测试完成 ==========');
  } catch (error: any) {
    if (error.name === 'AbortError') {
      addLog('warning', '测试已被用户取消');
    } else {
      console.error('[性能测试] 测试失败:', error);
      addLog('error', `测试失败: ${error}`);
      addLog('warning', '请检查 Ollama 服务是否正在运行 (http://localhost:11434)');
    }
  } finally {
    testing.value = false;
    abortController = null;
  }
};

const initChart = () => {
  if (!chartRef.value) return;
  
  chartInstance = echarts.init(chartRef.value);
  updateChart();
  
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
};

const updateChart = () => {
  if (!chartInstance) return;
  
  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9' },
    },
    legend: {
      data: ['生成速度 (tokens/s)', 'Prompt处理速度 (tokens/s)'],
      textStyle: { color: '#64748b' },
      top: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: testResults.value.map((_r, i) => `测试 ${testResults.value.length - i}`).reverse(),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
    },
    yAxis: {
      type: 'value',
      name: 'tokens/s',
      nameTextStyle: { color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [
      {
        name: '生成速度 (tokens/s)',
        type: 'line',
        smooth: true,
        data: [...testResults.value].reverse().map(r => r.eval_rate),
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
          ]),
        },
      },
      {
        name: 'Prompt处理速度 (tokens/s)',
        type: 'line',
        smooth: true,
        data: [...testResults.value].reverse().map(r => r.prompt_eval_rate),
        lineStyle: { color: '#22c55e', width: 2 },
        itemStyle: { color: '#22c55e' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
            { offset: 1, color: 'rgba(34, 197, 94, 0.05)' },
          ]),
        },
      },
    ],
  };
  
  chartInstance.setOption(option);
};

const clearResults = () => {
  testResults.value = [];
  currentResult.value = null;
  updateChart();
  addLog('info', '测试记录已清空');
};

const clearLogs = () => {
  logs.value = [];
};

onMounted(async () => {
  await loadModels();
  initChart();
});
</script>

<template>
  <div>
    <!-- Stats Overview -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px;">
      <div class="stat-card">
        <div class="stat-value">{{ avgEvalRate }}</div>
        <div class="stat-label">平均生成速度 (t/s)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ avgPromptRate }}</div>
        <div class="stat-label">平均处理速度 (t/s)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ testResults.length }}</div>
        <div class="stat-label">测试次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" :style="{ color: gpuUsagePercent > 50 ? '#22c55e' : '#f59e0b' }">
          {{ gpuUsagePercent }}%
        </div>
        <div class="stat-label">GPU 使用率</div>
      </div>
    </div>

    <!-- Test Configuration -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          性能测试
        </h3>
      </div>
      <div class="card-body">
        <div style="display: grid; grid-template-columns: 200px 1fr auto; gap: 12px; align-items: end;">
          <div>
            <label style="display: block; font-size: 13px; color: var(--color-text-muted); margin-bottom: 6px;">
              选择模型
            </label>
            <select v-model="selectedModel" class="select">
              <option v-for="model in models" :key="model.name" :value="model.name">
                {{ model.name }}
              </option>
            </select>
          </div>
          <div>
            <label style="display: block; font-size: 13px; color: var(--color-text-muted); margin-bottom: 6px;">
              测试 Prompt
            </label>
            <input 
              v-model="testPrompt"
              type="text" 
              class="input" 
              placeholder="输入测试 Prompt"
            />
          </div>
          <button 
            :class="['btn', testing ? 'btn-danger' : 'btn-primary']" 
            @click="runTest"
            :disabled="!selectedModel"
            style="height: 42px;"
          >
            <div v-if="testing" class="spinner"></div>
            <svg v-if="testing" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <rect x="6" y="6" width="12" height="12"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            {{ testing ? '停止测试' : '运行测试' }}
          </button>
        </div>
        
        <!-- Think 模式状态显示 -->
        <div style="margin-top: 16px; display: flex; align-items: center; gap: 12px;">
          <span :class="['badge', enableThink ? 'badge-success' : 'badge-neutral']">
            Think: {{ enableThink ? '开启' : '关闭' }}
          </span>
          <span v-if="isVisionModel" class="badge badge-info">
            视觉模型
          </span>
          <div style="font-size: 12px; color: var(--color-text-muted);">
            在「模型管理」→「预加载设置」中修改 Think 模式 · 使用 HTTP 流式 API 测试
          </div>
        </div>
        
        <!-- 视觉模型图像上传 -->
        <div v-if="isVisionModel" style="margin-top: 16px; padding: 16px; background: var(--color-bg-secondary); border-radius: 8px; border: 1px dashed var(--color-border);">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px; color: var(--color-primary);">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <span style="font-weight: 500;">图像输入（可选）</span>
          </div>
          
          <div v-if="!imagePreviewUrl" style="display: flex; gap: 12px;">
            <button class="btn btn-secondary" @click="selectImage" style="flex: 1;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              选择图像
            </button>
          </div>
          
          <div v-else style="display: flex; gap: 16px; align-items: flex-start;">
            <div style="position: relative;">
              <img 
                :src="imagePreviewUrl" 
                alt="Preview" 
                style="max-width: 200px; max-height: 150px; border-radius: 8px; border: 1px solid var(--color-border);"
              />
              <button 
                class="btn btn-danger" 
                @click="clearImage"
                style="position: absolute; top: -8px; right: -8px; width: 24px; height: 24px; padding: 0; border-radius: 50%;"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div style="flex: 1;">
              <div style="font-size: 13px; color: var(--color-text-muted); margin-bottom: 4px;">已选择图像:</div>
              <div style="font-size: 14px; word-break: break-all;">{{ selectedImagePath.split(/[/\\]/).pop() }}</div>
            </div>
          </div>
          
          <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 12px;">
            支持 PNG、JPG、GIF、WebP 格式。视觉模型可以理解图像内容并回答相关问题。
          </div>
        </div>
      </div>
    </div>

    <!-- Streaming Output -->
    <div v-if="testing || streamingOutput" class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          模型输出
          <span v-if="testing" class="badge badge-info" style="margin-left: 8px;">
            <div class="spinner" style="width: 12px; height: 12px;"></div>
            生成中...
          </span>
        </h3>
        <button v-if="!testing && streamingOutput" class="btn btn-secondary" @click="streamingOutput = ''; thinkingOutput = ''">
          清空
        </button>
      </div>
      <div class="card-body">
        <!-- 思考过程（如果有且开启显示） -->
        <div v-if="thinkingOutput && enableThink" style="margin-bottom: 16px;">
          <div style="font-size: 12px; color: var(--color-text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            思考过程
          </div>
          <div class="thinking-output">
            <pre style="margin: 0; white-space: pre-wrap; word-break: break-word;">{{ thinkingOutput }}</pre>
          </div>
        </div>
        
        <!-- 主要输出 -->
        <div>
          <div style="font-size: 12px; color: var(--color-text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            回复内容
          </div>
          <div class="streaming-output">
            <pre style="margin: 0; white-space: pre-wrap; word-break: break-word;">{{ streamingOutput || '等待输出...' }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Current Result -->
    <div v-if="currentResult" class="card" style="border-color: var(--color-primary);">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          最新测试结果
        </h3>
        <span :class="['badge', currentResult.processor.includes('GPU') ? 'badge-success' : 'badge-warning']">
          {{ currentResult.processor }}
        </span>
      </div>
      <div class="card-body">
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">模型</div>
            <div class="info-value">{{ currentResult.model }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">生成速度</div>
            <div class="info-value" style="color: var(--color-primary);">
              {{ currentResult.eval_rate.toFixed(2) }} tokens/s
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Prompt 处理速度</div>
            <div class="info-value" style="color: var(--color-success);">
              {{ currentResult.prompt_eval_rate.toFixed(2) }} tokens/s
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">总耗时</div>
            <div class="info-value">{{ currentResult.total_duration }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">生成 Token 数</div>
            <div class="info-value">{{ currentResult.eval_count }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">处理器</div>
            <div class="info-value">{{ currentResult.processor }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chart -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          性能趋势
        </h3>
        <button class="btn btn-secondary" @click="clearResults">
          清空记录
        </button>
      </div>
      <div class="card-body">
        <div 
          v-if="testResults.length === 0" 
          class="empty-state" 
          style="height: 280px; display: flex; flex-direction: column; justify-content: center;"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <p>暂无测试数据</p>
          <p style="font-size: 13px; margin-top: 8px;">运行测试后将显示性能趋势图</p>
        </div>
        <div v-else ref="chartRef" style="height: 280px;"></div>
      </div>
    </div>

    <!-- Test History -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          测试历史
        </h3>
      </div>
      <div class="card-body">
        <div v-if="testResults.length === 0" class="empty-state" style="padding: 32px;">
          <p>暂无测试记录</p>
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>模型</th>
                <th>生成速度</th>
                <th>处理速度</th>
                <th>总耗时</th>
                <th>处理器</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(result, index) in testResults" :key="index">
                <td><strong>{{ result.model }}</strong></td>
                <td style="color: var(--color-primary); font-weight: 500;">
                  {{ result.eval_rate.toFixed(2) }} t/s
                </td>
                <td style="color: var(--color-success); font-weight: 500;">
                  {{ result.prompt_eval_rate.toFixed(2) }} t/s
                </td>
                <td>{{ result.total_duration }}</td>
                <td>
                  <span :class="['badge', result.processor.includes('GPU') ? 'badge-success' : 'badge-warning']">
                    {{ result.processor }}
                  </span>
                </td>
                <td style="color: var(--color-text-muted);">{{ result.timestamp }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Operation Logs -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          操作日志
        </h3>
        <button class="btn btn-secondary" @click="clearLogs">
          清空
        </button>
      </div>
      <div class="card-body">
        <div ref="logViewerRef" class="log-viewer">
          <div v-if="logs.length === 0" style="color: #64748b;">
            暂无日志，点击"运行测试"开始测试...
          </div>
          <div 
            v-for="(log, index) in logs" 
            :key="index" 
            :class="['log-line', log.type]"
          >
            {{ log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
