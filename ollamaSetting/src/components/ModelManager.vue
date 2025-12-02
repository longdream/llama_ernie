<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';

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

interface DownloadProgress {
  model: string;
  progress: number;
  status: string;
}

interface PreloadResult {
  success: boolean;
  model: string;
  message: string;
  load_duration: string;
}

interface ImportResult {
  success: boolean;
  model_name: string;
  message: string;
}

const loading = ref(false);
const pulling = ref(false);
const preloading = ref<string | null>(null);
const importing = ref(false);
const models = ref<Model[]>([]);
const runningModels = ref<RunningModel[]>([]);
const modelInput = ref('qwen3:30b-a3b');
const downloadProgress = ref<DownloadProgress | null>(null);
const pullOutput = ref('');

// 导入 GGUF 相关
const ggufPath = ref('');
const ggufModelName = ref('');
const importOutput = ref('');

// 操作日志
const operationLogs = ref<{ type: string; message: string }[]>([]);
const logViewerRef = ref<HTMLDivElement | null>(null);

const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  operationLogs.value.push({ type, message: `[${timestamp}] ${message}` });
  // 自动滚动到底部
  nextTick(() => {
    if (logViewerRef.value) {
      logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight;
    }
  });
};

const clearLogs = () => {
  operationLogs.value = [];
};

// Keep Alive 选项
const keepAliveOptions = [
  { value: 'default', label: '默认 (5分钟)' },
  { value: '5m', label: '5 分钟' },
  { value: '30m', label: '30 分钟' },
  { value: '1h', label: '1 小时' },
  { value: '24h', label: '24 小时' },
  { value: '-1', label: '永久保留' },
];
const selectedKeepAlive = ref('default');

// Think 模式开关（Qwen3 等模型支持）
// 关闭时会在请求中添加 /no_think 指令
const enableThink = ref(localStorage.getItem('ollama_enable_think') === 'true');

// 监听 Think 模式变化，保存到 localStorage
watch(enableThink, (newValue) => {
  localStorage.setItem('ollama_enable_think', newValue ? 'true' : 'false');
});

// ==================== 保活功能 ====================
const KEEP_ALIVE_INTERVAL = 4 * 60 * 1000;  // 4 分钟检测间隔
const keepAliveEnabled = ref(localStorage.getItem('ollama_keep_alive_enabled') === 'true');  // 保活开关
const protectedModels = ref<Set<string>>(new Set());  // 受保护的模型列表
let keepAliveTimer: ReturnType<typeof setInterval> | null = null;  // 定时器 ID

// 检测并重新加载被卸载的模型
const checkAndReloadModels = async () => {
  if (!keepAliveEnabled.value || protectedModels.value.size === 0) return;
  
  await loadRunningModels();
  
  for (const modelName of protectedModels.value) {
    if (!isModelRunning(modelName)) {
      addLog('warning', `检测到模型 ${modelName} 已卸载，正在自动重新加载...`);
      await preloadModelInternal(modelName, true);  // 内部调用，标记为自动重载
    }
  }
};

// 启动保活定时器
const startKeepAliveTimer = () => {
  if (keepAliveTimer) {
    clearInterval(keepAliveTimer);
  }
  keepAliveTimer = setInterval(checkAndReloadModels, KEEP_ALIVE_INTERVAL);
  addLog('info', `保活模式已启用，每 ${KEEP_ALIVE_INTERVAL / 60000} 分钟检测一次`);
};

// 停止保活定时器
const stopKeepAliveTimer = () => {
  if (keepAliveTimer) {
    clearInterval(keepAliveTimer);
    keepAliveTimer = null;
  }
  protectedModels.value.clear();
  addLog('info', '保活模式已关闭，已清空受保护模型列表');
};

// 监听保活开关变化
watch(keepAliveEnabled, (enabled) => {
  localStorage.setItem('ollama_keep_alive_enabled', enabled ? 'true' : 'false');
  if (enabled) {
    startKeepAliveTimer();
  } else {
    stopKeepAliveTimer();
  }
});

const recommendedModels = [
  { name: 'qwen3:30b-a3b', desc: 'Qwen3 30B MoE 模型，推荐', size: '~18GB' },
  { name: 'qwen3:8b', desc: 'Qwen3 8B 基础模型', size: '~5GB' },
  { name: 'llama3.2:3b', desc: 'Llama 3.2 3B 轻量模型', size: '~2GB' },
  { name: 'deepseek-r1:14b', desc: 'DeepSeek R1 14B', size: '~9GB' },
  { name: 'gemma2:9b', desc: 'Google Gemma 2 9B', size: '~5GB' },
  { name: 'phi3:mini', desc: 'Microsoft Phi-3 Mini', size: '~2GB' },
];

const loadModels = async () => {
  loading.value = true;
  try {
    models.value = await invoke<Model[]>('list_ollama_models');
    // 同时加载运行中的模型
    await loadRunningModels();
  } catch (error) {
    console.error('Failed to load models:', error);
    addLog('error', `加载模型列表失败: ${error}`);
  } finally {
    loading.value = false;
  }
};

const loadRunningModels = async () => {
  try {
    const result = await invoke<RunningModel[]>('get_running_models');
    runningModels.value = result;
    console.log('[loadRunningModels] 运行中的模型:', result.map(m => m.name));
  } catch (error) {
    console.error('Failed to load running models:', error);
    runningModels.value = [];
  }
};

// 检查模型是否已加载（精确匹配模型名称）
const isModelRunning = (modelName: string): boolean => {
  // 标准化模型名称：如果没有标签，添加 :latest
  const normalize = (name: string) => name.includes(':') ? name : `${name}:latest`;
  const normalizedInput = normalize(modelName);
  
  return runningModels.value.some(m => {
    const normalizedRunning = normalize(m.name);
    // 完全匹配（标准化后）
    return normalizedRunning === normalizedInput;
  });
};

// 获取模型运行信息（精确匹配模型名称）
const getModelRunningInfo = (modelName: string): RunningModel | undefined => {
  const normalize = (name: string) => name.includes(':') ? name : `${name}:latest`;
  const normalizedInput = normalize(modelName);
  
  return runningModels.value.find(m => {
    const normalizedRunning = normalize(m.name);
    return normalizedRunning === normalizedInput;
  });
};

const pullModel = async (name?: string) => {
  const modelName = name || modelInput.value.trim();
  if (!modelName) return;
  
  pulling.value = true;
  pullOutput.value = '';
  downloadProgress.value = { model: modelName, progress: 0, status: '准备下载...' };
  
  addLog('info', `========== 开始下载模型 ==========`);
  addLog('info', `模型名称: ${modelName}`);
  
  try {
    const result = await invoke<string>('pull_ollama_model', { modelName });
    pullOutput.value = result;
    downloadProgress.value = { model: modelName, progress: 100, status: '下载完成!' };
    addLog('success', `模型 ${modelName} 下载完成`);
    await loadModels();
  } catch (error) {
    pullOutput.value = `下载失败: ${error}`;
    addLog('error', `下载失败: ${error}`);
    downloadProgress.value = null;
  } finally {
    pulling.value = false;
    setTimeout(() => {
      downloadProgress.value = null;
    }, 3000);
  }
};

const deleteModel = async (name: string) => {
  if (!confirm(`确定要删除模型 "${name}" 吗？`)) return;
  
  addLog('info', `正在删除模型: ${name}`);
  try {
    await invoke('delete_ollama_model', { modelName: name });
    addLog('success', `模型 ${name} 已删除`);
    await loadModels();
  } catch (error) {
    console.error('Failed to delete model:', error);
    addLog('error', `删除失败: ${error}`);
    alert(`删除失败: ${error}`);
  }
};

const selectModel = (name: string) => {
  modelInput.value = name;
};

// ==================== 预加载功能 ====================

// 内部预加载函数，支持标记是否为自动重载
const preloadModelInternal = async (modelName: string, isAutoReload: boolean = false) => {
  preloading.value = modelName;
  
  if (isAutoReload) {
    addLog('info', `========== 自动重新加载模型 ==========`);
  } else {
    addLog('info', `========== 开始预加载模型 ==========`);
  }
  addLog('info', `模型: ${modelName}`);
  addLog('info', `Keep Alive: ${selectedKeepAlive.value === 'default' ? '默认(5分钟)' : selectedKeepAlive.value}`);
  
  // 显示当前运行中的模型
  if (runningModels.value.length > 0) {
    addLog('info', `当前运行中: ${runningModels.value.map(m => m.name).join(', ')}`);
  }
  
  try {
    const startTime = Date.now();
    const result = await invoke<PreloadResult>('preload_model', { 
      modelName, 
      keepAlive: selectedKeepAlive.value 
    });
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    
    if (result.success) {
      pullOutput.value = `✅ ${result.message}\n加载耗时: ${result.load_duration}`;
      addLog('success', result.message);
      addLog('info', `加载耗时: ${result.load_duration}`);
      addLog('info', `总操作耗时: ${elapsed} 秒`);
      
      // 如果保活模式开启，将模型加入保护列表
      if (keepAliveEnabled.value) {
        protectedModels.value.add(modelName);
        addLog('info', `模型 ${modelName} 已加入保活保护列表`);
      }
    }
    await loadRunningModels();
    addLog('success', `========== 预加载完成 ==========`);
  } catch (error) {
    pullOutput.value = `❌ 预加载失败: ${error}`;
    addLog('error', `预加载失败: ${error}`);
    addLog('warning', '请检查 Ollama 服务是否正在运行');
  } finally {
    preloading.value = null;
  }
};

// 用户手动预加载模型
const preloadModel = async (modelName: string) => {
  await preloadModelInternal(modelName, false);
};

const unloadModel = async (modelName: string) => {
  addLog('info', `正在卸载模型: ${modelName}`);
  
  // 用户手动卸载时，从保护列表中移除该模型（防止自动重载）
  if (protectedModels.value.has(modelName)) {
    protectedModels.value.delete(modelName);
    addLog('info', `模型 ${modelName} 已从保活保护列表中移除`);
  }
  
  try {
    const result = await invoke<string>('unload_model', { modelName });
    pullOutput.value = `✅ ${result}`;
    addLog('success', `${result}`);
    await loadRunningModels();
  } catch (error) {
    pullOutput.value = `❌ 卸载失败: ${error}`;
    addLog('error', `卸载失败: ${error}`);
  }
};

// ==================== 导入 GGUF 功能 ====================

const selectGgufFile = async () => {
  try {
    const selected = await open({
      multiple: false,
      filters: [{
        name: 'GGUF Model',
        extensions: ['gguf']
      }]
    });
    if (selected) {
      ggufPath.value = selected as string;
      // 自动从文件名生成模型名
      const fileName = ggufPath.value.split(/[/\\]/).pop() || '';
      const baseName = fileName.replace('.gguf', '').replace(/[-_]Q\d.*$/i, '');
      ggufModelName.value = baseName.toLowerCase().replace(/[^a-z0-9-]/g, '-');
    }
  } catch (error) {
    console.error('Failed to select file:', error);
  }
};

const importGgufModel = async () => {
  if (!ggufPath.value || !ggufModelName.value) {
    importOutput.value = '❌ 请选择 GGUF 文件并输入模型名称';
    addLog('warning', '请选择 GGUF 文件并输入模型名称');
    return;
  }
  
  importing.value = true;
  importOutput.value = '正在导入模型，请稍候...';
  
  addLog('info', `========== 开始导入 GGUF 模型 ==========`);
  addLog('info', `文件路径: ${ggufPath.value}`);
  addLog('info', `模型名称: ${ggufModelName.value}`);
  
  try {
    const result = await invoke<ImportResult>('import_gguf_model', {
      ggufPath: ggufPath.value,
      modelName: ggufModelName.value
    });
    
    if (result.success) {
      importOutput.value = `✅ ${result.message}`;
      addLog('success', `${result.message}`);
      // 清空输入
      ggufPath.value = '';
      ggufModelName.value = '';
      // 刷新模型列表
      await loadModels();
    } else {
      importOutput.value = `❌ 导入失败: ${result.message}`;
      addLog('error', `导入失败: ${result.message}`);
    }
  } catch (error) {
    importOutput.value = `❌ 导入失败: ${error}`;
    addLog('error', `导入失败: ${error}`);
  } finally {
    importing.value = false;
  }
};

onMounted(() => {
  loadModels();
  // 如果保活模式之前是开启的，恢复定时器
  if (keepAliveEnabled.value) {
    startKeepAliveTimer();
  }
});

// 组件卸载时清理定时器
onUnmounted(() => {
  if (keepAliveTimer) {
    clearInterval(keepAliveTimer);
    keepAliveTimer = null;
  }
});
</script>

<template>
  <div>
    <!-- Download Progress -->
    <div v-if="downloadProgress" class="card" style="border-color: var(--color-primary);">
      <div class="card-body">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div>
            <div style="font-weight: 600;">正在下载: {{ downloadProgress.model }}</div>
            <div style="font-size: 13px; color: var(--color-text-muted);">{{ downloadProgress.status }}</div>
          </div>
          <span class="badge badge-info">{{ downloadProgress.progress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: downloadProgress.progress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Import GGUF Model -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
          </svg>
          导入本地 GGUF 模型
        </h3>
      </div>
      <div class="card-body">
        <div style="display: flex; gap: 12px; margin-bottom: 12px;">
          <input 
            v-model="ggufPath"
            type="text" 
            class="input" 
            placeholder="选择 GGUF 模型文件..."
            style="flex: 1;"
            readonly
          />
          <button class="btn btn-secondary" @click="selectGgufFile">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            浏览
          </button>
        </div>
        <div style="display: flex; gap: 12px; margin-bottom: 12px;">
          <input 
            v-model="ggufModelName"
            type="text" 
            class="input" 
            placeholder="输入模型名称（如 my-model）"
            style="flex: 1;"
          />
          <button 
            class="btn btn-primary" 
            @click="importGgufModel"
            :disabled="importing || !ggufPath || !ggufModelName"
          >
            <div v-if="importing" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            导入
          </button>
        </div>
        <div v-if="importOutput" class="log-viewer" style="margin-top: 12px; max-height: 100px;">
          <pre style="margin: 0; white-space: pre-wrap;">{{ importOutput }}</pre>
        </div>
        <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 8px;">
          支持从本地导入 .gguf 格式的模型文件，导入后可在 Ollama 中使用
        </div>
      </div>
    </div>

    <!-- Pull Model -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          下载模型
        </h3>
      </div>
      <div class="card-body">
        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
          <input 
            v-model="modelInput"
            type="text" 
            class="input" 
            placeholder="输入模型名称，如 qwen3:30b-a3b"
            style="flex: 1;"
            @keyup.enter="pullModel()"
          />
          <button 
            class="btn btn-primary" 
            @click="pullModel()"
            :disabled="pulling || !modelInput.trim()"
          >
            <div v-if="pulling" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            下载
          </button>
        </div>

        <div style="font-size: 13px; color: var(--color-text-muted); margin-bottom: 12px;">推荐模型：</div>
        <div class="download-grid">
          <div 
            v-for="model in recommendedModels" 
            :key="model.name" 
            class="download-card"
            @click="selectModel(model.name)"
            style="cursor: pointer;"
          >
            <div class="download-card-header">
              <span class="download-card-title">{{ model.name }}</span>
              <span class="badge badge-neutral">{{ model.size }}</span>
            </div>
            <div class="download-card-desc">{{ model.desc }}</div>
            <button 
              class="btn btn-secondary" 
              style="width: 100%;"
              @click.stop="pullModel(model.name)"
              :disabled="pulling"
            >
              下载此模型
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Preload Settings -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          预加载设置
        </h3>
      </div>
      <div class="card-body">
        <div class="setting-item" style="display: flex; align-items: center; gap: 16px;">
          <div class="setting-info" style="flex: 1;">
            <div class="setting-label">Keep Alive 时间</div>
            <div class="setting-desc">模型加载后在内存中保留的时间</div>
          </div>
          <select v-model="selectedKeepAlive" class="input" style="width: 160px;">
            <option v-for="opt in keepAliveOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        
        <!-- Think 模式开关 -->
        <div class="setting-item" style="display: flex; align-items: center; gap: 16px;">
          <div class="setting-info" style="flex: 1;">
            <div class="setting-label">Think 模式</div>
            <div class="setting-desc">启用后模型会输出思考过程（Qwen3 等模型支持），关闭可减少 token 数量</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="enableThink" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        
        <!-- 保活模式开关 -->
        <div class="setting-item" style="display: flex; align-items: center; gap: 16px;">
          <div class="setting-info" style="flex: 1;">
            <div class="setting-label">
              保活模式
              <span v-if="keepAliveEnabled && protectedModels.size > 0" class="badge badge-success" style="margin-left: 8px;">
                {{ protectedModels.size }} 个模型受保护
              </span>
            </div>
            <div class="setting-desc">启用后每 4 分钟检测模型状态，若模型因超时被卸载会自动重新加载（手动卸载不会触发）</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="keepAliveEnabled" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        
        <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 8px;">
          提示：预加载可以减少首次推理的等待时间，设置较长的 Keep Alive 可避免频繁重新加载
        </div>
      </div>
    </div>

    <!-- Installed Models -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          已安装的模型
        </h3>
        <button class="btn btn-secondary" @click="loadModels" :disabled="loading">
          <div v-if="loading" class="spinner"></div>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
            <path d="M23 4v6h-6"/>
            <path d="M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          刷新
        </button>
      </div>
      <div class="card-body">
        <div v-if="loading" style="text-align: center; padding: 32px;">
          <div class="spinner" style="margin: 0 auto 16px;"></div>
          <p style="color: var(--color-text-muted);">加载中...</p>
        </div>

        <div v-else-if="models.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          <p>暂无已安装的模型</p>
          <p style="font-size: 13px; margin-top: 8px;">使用上方表单下载或导入模型</p>
        </div>

        <div v-else>
          <div v-for="model in models" :key="model.name" class="model-item">
            <div class="model-info">
              <div class="model-name">
                {{ model.name }}
                <span v-if="isModelRunning(model.name)" class="badge badge-success" style="margin-left: 8px;">
                  运行中
                </span>
              </div>
              <div class="model-meta">
                大小: {{ model.size }} · 修改时间: {{ model.modified }}
                <template v-if="getModelRunningInfo(model.name)">
                  · 处理器: {{ getModelRunningInfo(model.name)?.processor }}
                  · 上下文: {{ getModelRunningInfo(model.name)?.context }}
                </template>
              </div>
            </div>
            <div class="model-actions">
              <!-- 预加载/卸载按钮 -->
              <button 
                v-if="!isModelRunning(model.name)"
                class="btn btn-primary" 
                @click="preloadModel(model.name)"
                :disabled="preloading === model.name"
              >
                <div v-if="preloading === model.name" class="spinner"></div>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                预加载
              </button>
              <button 
                v-else
                class="btn btn-warning" 
                @click="unloadModel(model.name)"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                  <rect x="6" y="4" width="4" height="16"/>
                  <rect x="14" y="4" width="4" height="16"/>
                </svg>
                卸载
              </button>
              
              <button class="btn btn-danger" @click="deleteModel(model.name)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pull Output -->
    <div v-if="pullOutput" class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          下载日志
        </h3>
        <button class="btn btn-secondary" @click="pullOutput = ''">
          清空
        </button>
      </div>
      <div class="card-body">
        <div class="log-viewer">
          <pre style="margin: 0; white-space: pre-wrap;">{{ pullOutput }}</pre>
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
          <div v-if="operationLogs.length === 0" style="color: #64748b;">
            暂无日志，操作模型后将显示日志...
          </div>
          <div 
            v-for="(log, index) in operationLogs" 
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
