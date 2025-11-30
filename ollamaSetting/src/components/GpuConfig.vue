<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { invoke } from '@tauri-apps/api/core';

interface GpuInfo {
  name: string;
  adapter_ram: number;
  driver_version: string;
  is_intel_arc: boolean;
  vulkan_supported: boolean;
}

interface OllamaStatus {
  name: string;
  id: string;
  size: string;
  processor: string;
  context: string;
  until: string;
}

const loading = ref(false);
const configuring = ref(false);
const restarting = ref(false);
const intelGpu = ref<GpuInfo | null>(null);
const runningModels = ref<OllamaStatus[]>([]);
const logs = ref<{ type: string; message: string }[]>([]);

const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  logs.value.push({ type, message: `[${timestamp}] ${message}` });
};

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const detectGpu = async () => {
  loading.value = true;
  addLog('info', '正在检测 Intel GPU...');
  
  try {
    const gpu = await invoke<GpuInfo | null>('get_intel_gpu');
    intelGpu.value = gpu;
    
    if (gpu) {
      addLog('success', `检测到 Intel GPU: ${gpu.name}`);
      addLog('info', `显存: ${formatBytes(gpu.adapter_ram)}, 驱动版本: ${gpu.driver_version}`);
    } else {
      addLog('warning', '未检测到 Intel Arc GPU');
    }
  } catch (error) {
    addLog('error', `GPU 检测失败: ${error}`);
  } finally {
    loading.value = false;
  }
};

const loadRunningModels = async () => {
  try {
    runningModels.value = await invoke<OllamaStatus[]>('get_running_models');
  } catch (error) {
    console.error('Failed to get running models:', error);
  }
};

const configureVulkan = async () => {
  configuring.value = true;
  addLog('info', '正在配置 Ollama Vulkan 环境变量...');
  
  try {
    const result = await invoke<string>('configure_ollama_vulkan');
    addLog('success', result);
    addLog('info', '环境变量已设置: OLLAMA_VULKAN=1, ZES_ENABLE_SYSMAN=1');
  } catch (error) {
    addLog('error', `配置失败: ${error}`);
  } finally {
    configuring.value = false;
  }
};

const restartOllama = async () => {
  restarting.value = true;
  addLog('info', '正在重启 Ollama 服务...');
  
  try {
    const result = await invoke<string>('restart_ollama_service');
    addLog('success', result);
    
    setTimeout(async () => {
      await loadRunningModels();
      restarting.value = false;
    }, 3000);
  } catch (error) {
    addLog('error', `重启失败: ${error}`);
    restarting.value = false;
  }
};

const oneClickSetup = async () => {
  logs.value = [];
  await detectGpu();
  
  if (!intelGpu.value) {
    addLog('warning', '未检测到 Intel Arc GPU，但仍可尝试配置 Vulkan');
  }
  
  await configureVulkan();
  await restartOllama();
  
  addLog('success', '✓ 一键配置完成！请等待 Ollama 服务启动后测试。');
};

const ipexConfiguring = ref(false);

const configureIpexLlm = async () => {
  ipexConfiguring.value = true;
  addLog('info', '正在配置 IPEX-LLM 优化环境变量...');
  
  try {
    const result = await invoke<string>('configure_ipex_llm');
    addLog('success', result);
    addLog('info', '环境变量已设置: OLLAMA_NUM_GPU=999, SYCL_CACHE_PERSISTENT=1, OLLAMA_INTEL_GPU=1');
  } catch (error) {
    addLog('error', `IPEX-LLM 配置失败: ${error}`);
  } finally {
    ipexConfiguring.value = false;
  }
};

const oneClickIpexSetup = async () => {
  logs.value = [];
  await detectGpu();
  
  if (!intelGpu.value) {
    addLog('warning', '未检测到 Intel Arc GPU，但仍可尝试配置 IPEX-LLM');
  }
  
  await configureIpexLlm();
  await restartOllama();
  
  addLog('success', '✓ IPEX-LLM 一键优化完成！请等待 Ollama 服务启动后测试。');
};

onMounted(async () => {
  await detectGpu();
  await loadRunningModels();
});
</script>

<template>
  <div>
    <!-- Alert -->
    <div v-if="intelGpu" class="alert alert-success">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <div class="alert-content">
        <div class="alert-title">检测到 Intel Arc GPU</div>
        <div class="alert-desc">{{ intelGpu.name }} - 可以启用 Vulkan 加速</div>
      </div>
    </div>

    <div v-else-if="!loading" class="alert alert-warning">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <div class="alert-content">
        <div class="alert-title">未检测到 Intel Arc GPU</div>
        <div class="alert-desc">请确保已安装 Intel Arc 显卡和最新驱动程序</div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          快速操作
        </h3>
      </div>
      <div class="card-body">
        <div class="action-bar">
          <button 
            class="btn btn-primary" 
            @click="oneClickSetup"
            :disabled="loading || configuring || restarting"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            一键配置 Intel GPU
          </button>
          
          <button 
            class="btn btn-secondary" 
            @click="detectGpu"
            :disabled="loading"
          >
            <div v-if="loading" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            检测 GPU
          </button>
          
          <button 
            class="btn btn-secondary" 
            @click="configureVulkan"
            :disabled="configuring"
          >
            <div v-if="configuring" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09"/>
            </svg>
            配置 Vulkan
          </button>
          
          <button 
            class="btn btn-success" 
            @click="restartOllama"
            :disabled="restarting"
          >
            <div v-if="restarting" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            重启 Ollama
          </button>
        </div>
      </div>
    </div>

    <!-- GPU Status -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <rect x="8" y="8" width="8" height="8" rx="1"/>
          </svg>
          Intel GPU 状态
        </h3>
        <span :class="['badge', intelGpu ? 'badge-success' : 'badge-warning']">
          {{ intelGpu ? '已检测' : '未检测到' }}
        </span>
      </div>
      <div class="card-body">
        <template v-if="intelGpu">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">GPU 型号</div>
              <div class="setting-desc">检测到的 Intel GPU</div>
            </div>
            <div class="setting-value">{{ intelGpu.name }}</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">显存大小</div>
              <div class="setting-desc">GPU 可用显存</div>
            </div>
            <div class="setting-value">{{ formatBytes(intelGpu.adapter_ram) }}</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">驱动版本</div>
              <div class="setting-desc">当前安装的驱动</div>
            </div>
            <div class="setting-value">{{ intelGpu.driver_version }}</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">Vulkan 支持</div>
              <div class="setting-desc">是否支持 Vulkan 加速</div>
            </div>
            <div 
              class="toggle" 
              :class="{ active: intelGpu.vulkan_supported }"
            ></div>
          </div>
        </template>

        <div v-else class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <rect x="8" y="8" width="8" height="8" rx="1"/>
          </svg>
          <p>未检测到 Intel Arc GPU</p>
          <p style="font-size: 13px; margin-top: 8px;">请确保已安装 Intel Arc 显卡和最新驱动</p>
        </div>
      </div>
    </div>

    <!-- Running Models -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          运行中的模型
        </h3>
        <button class="btn btn-icon btn-secondary" @click="loadRunningModels">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
            <path d="M23 4v6h-6"/>
            <path d="M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </button>
      </div>
      <div class="card-body">
        <div v-if="runningModels.length === 0" class="empty-state" style="padding: 32px;">
          <p>当前没有运行中的模型</p>
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>模型</th>
                <th>大小</th>
                <th>处理器</th>
                <th>上下文</th>
                <th>过期时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="model in runningModels" :key="model.id">
                <td>
                  <strong>{{ model.name }}</strong>
                  <div style="font-size: 12px; color: var(--color-text-muted);">{{ model.id }}</div>
                </td>
                <td>{{ model.size }}</td>
                <td>
                  <span :class="['badge', model.processor.includes('GPU') ? 'badge-success' : 'badge-info']">
                    {{ model.processor }}
                  </span>
                </td>
                <td>{{ model.context }}</td>
                <td>{{ model.until }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Intel IPEX-LLM One-Click Optimization -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          Intel IPEX-LLM 一键优化
        </h3>
        <span class="badge badge-success">推荐</span>
      </div>
      <div class="card-body">
        <div class="alert alert-info" style="margin-bottom: 16px;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <div class="alert-content">
            <div class="alert-title">IPEX-LLM 优化说明</div>
            <div class="alert-desc">
              一键配置 Intel GPU 优化环境变量，提升大模型推理性能，支持 INT4/FP4 低精度推理。
            </div>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">将配置的环境变量</div>
            <div class="setting-desc">点击一键优化后将自动设置以下环境变量</div>
          </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px;">
          <div style="padding: 12px; background: var(--color-bg-secondary); border-radius: 8px;">
            <div style="font-weight: 600; font-family: monospace; color: var(--color-primary);">OLLAMA_NUM_GPU=999</div>
            <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 4px;">使用所有 GPU 层</div>
          </div>
          <div style="padding: 12px; background: var(--color-bg-secondary); border-radius: 8px;">
            <div style="font-weight: 600; font-family: monospace; color: var(--color-primary);">SYCL_CACHE_PERSISTENT=1</div>
            <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 4px;">启用 SYCL 缓存</div>
          </div>
          <div style="padding: 12px; background: var(--color-bg-secondary); border-radius: 8px;">
            <div style="font-weight: 600; font-family: monospace; color: var(--color-primary);">OLLAMA_INTEL_GPU=1</div>
            <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 4px;">启用 Intel GPU 支持</div>
          </div>
          <div style="padding: 12px; background: var(--color-bg-secondary); border-radius: 8px;">
            <div style="font-weight: 600; font-family: monospace; color: var(--color-primary);">ZES_ENABLE_SYSMAN=1</div>
            <div style="font-size: 12px; color: var(--color-text-muted); margin-top: 4px;">启用系统管理</div>
          </div>
        </div>

        <div class="action-bar">
          <button 
            class="btn btn-primary" 
            @click="oneClickIpexSetup"
            :disabled="loading || ipexConfiguring || restarting"
          >
            <div v-if="ipexConfiguring" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            一键优化 IPEX-LLM
          </button>
          
          <button 
            class="btn btn-secondary" 
            @click="configureIpexLlm"
            :disabled="ipexConfiguring"
          >
            <div v-if="ipexConfiguring" class="spinner"></div>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09"/>
            </svg>
            仅配置环境变量
          </button>
        </div>
      </div>
    </div>

    <!-- Logs -->
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
        <button class="btn btn-secondary" @click="logs = []">
          清空
        </button>
      </div>
      <div class="card-body">
        <div class="log-viewer">
          <div v-if="logs.length === 0" style="color: #64748b;">
            暂无日志...
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
