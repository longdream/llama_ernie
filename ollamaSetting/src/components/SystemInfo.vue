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

interface OllamaVersion {
  installed: boolean;
  version: string;
}

interface EnvConfig {
  ollama_vulkan: string | null;
  zes_enable_sysman: string | null;
  ollama_host: string | null;
  ollama_models: string | null;
}

interface SystemInfo {
  cpu_name: string;
  total_memory: number;
  os_version: string;
}

const loading = ref(true);
const saving = ref(false);
const gpus = ref<GpuInfo[]>([]);
const ollamaVersion = ref<OllamaVersion>({ installed: false, version: '' });
const envConfig = ref<EnvConfig>({
  ollama_vulkan: null,
  zes_enable_sysman: null,
  ollama_host: null,
  ollama_models: null,
});
const systemInfo = ref<SystemInfo>({
  cpu_name: '',
  total_memory: 0,
  os_version: '',
});
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null);

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const loadData = async () => {
  loading.value = true;
  message.value = null;
  try {
    const [gpuData, ollamaData, envData, sysData] = await Promise.all([
      invoke<GpuInfo[]>('detect_gpu'),
      invoke<OllamaVersion>('check_ollama_installed'),
      invoke<EnvConfig>('get_env_config'),
      invoke<SystemInfo>('get_system_info'),
    ]);
    
    gpus.value = gpuData;
    ollamaVersion.value = ollamaData;
    envConfig.value = envData;
    systemInfo.value = sysData;
  } catch (error) {
    console.error('Failed to load system info:', error);
    message.value = { type: 'error', text: `加载失败: ${error}` };
  } finally {
    loading.value = false;
  }
};

const toggleEnvVar = async (name: string, currentValue: string | null) => {
  saving.value = true;
  message.value = null;
  
  try {
    const newValue = currentValue === '1' ? '0' : '1';
    await invoke('set_env_variable', { 
      name, 
      value: newValue, 
      systemWide: false 
    });
    
    // Refresh env config
    const envData = await invoke<EnvConfig>('get_env_config');
    envConfig.value = envData;
    
    message.value = { 
      type: 'success', 
      text: `${name} 已${newValue === '1' ? '启用' : '禁用'}，重启 Ollama 后生效` 
    };
  } catch (error) {
    console.error('Failed to set env variable:', error);
    message.value = { type: 'error', text: `设置失败: ${error}` };
  } finally {
    saving.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div>
    <!-- Message -->
    <div v-if="message" :class="['alert', message.type === 'success' ? 'alert-success' : 'alert-warning']" style="margin-bottom: 16px;">
      <svg v-if="message.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
        <polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <div class="alert-content">
        <div class="alert-desc">{{ message.text }}</div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body" style="text-align: center; padding: 48px;">
        <div class="spinner" style="margin: 0 auto 16px;"></div>
        <p style="color: var(--color-text-muted);">正在检测系统信息...</p>
      </div>
    </div>

    <template v-else>
      <!-- System Overview -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            系统概览
          </h3>
          <button class="btn btn-secondary" @click="loadData" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
              <path d="M23 4v6h-6"/>
              <path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            刷新
          </button>
        </div>
        <div class="card-body">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">操作系统</div>
              <div class="setting-desc">当前运行的操作系统</div>
            </div>
            <div class="setting-value">Windows</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">处理器</div>
              <div class="setting-desc">CPU 型号</div>
            </div>
            <div class="setting-value">{{ systemInfo.cpu_name || '检测中...' }}</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">内存</div>
              <div class="setting-desc">系统总内存</div>
            </div>
            <div class="setting-value">{{ formatBytes(systemInfo.total_memory) }}</div>
          </div>
        </div>
      </div>

      <!-- Ollama Status -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            Ollama 状态
          </h3>
          <span :class="['badge', ollamaVersion.installed ? 'badge-success' : 'badge-danger']">
            {{ ollamaVersion.installed ? '已安装' : '未安装' }}
          </span>
        </div>
        <div class="card-body">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">安装状态</div>
              <div class="setting-desc">Ollama 是否已正确安装</div>
            </div>
            <span :class="['badge', ollamaVersion.installed ? 'badge-success' : 'badge-danger']">
              {{ ollamaVersion.installed ? '已安装' : '未检测到' }}
            </span>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">版本号</div>
              <div class="setting-desc">当前安装的 Ollama 版本</div>
            </div>
            <div class="setting-value">{{ ollamaVersion.version || 'N/A' }}</div>
          </div>
        </div>
      </div>

      <!-- GPU Information -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
              <rect x="8" y="8" width="8" height="8" rx="1"/>
            </svg>
            GPU 信息
          </h3>
          <span v-if="gpus.some(g => g.is_intel_arc)" class="badge badge-success">
            检测到 Intel Arc
          </span>
        </div>
        <div class="card-body">
          <div v-if="gpus.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
              <rect x="8" y="8" width="8" height="8" rx="1"/>
            </svg>
            <p>未检测到独立显卡</p>
          </div>

          <div v-else>
            <div v-for="(gpu, index) in gpus" :key="index" class="model-item">
              <div class="model-info">
                <div class="model-name">{{ gpu.name }}</div>
                <div class="model-meta">
                  显存: {{ formatBytes(gpu.adapter_ram) }} · 驱动: {{ gpu.driver_version }}
                </div>
              </div>
              <div class="model-actions">
                <span v-if="gpu.is_intel_arc" class="badge badge-info">Intel Arc</span>
                <span v-if="gpu.vulkan_supported" class="badge badge-success">Vulkan</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Environment Variables -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            环境变量配置
          </h3>
        </div>
        <div class="card-body">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">OLLAMA_VULKAN</div>
              <div class="setting-desc">启用 Vulkan GPU 加速</div>
            </div>
            <div 
              class="toggle" 
              :class="{ active: envConfig.ollama_vulkan === '1', disabled: saving }"
              @click="toggleEnvVar('OLLAMA_VULKAN', envConfig.ollama_vulkan)"
              style="cursor: pointer;"
            ></div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">ZES_ENABLE_SYSMAN</div>
              <div class="setting-desc">启用 Intel 系统管理</div>
            </div>
            <div 
              class="toggle" 
              :class="{ active: envConfig.zes_enable_sysman === '1', disabled: saving }"
              @click="toggleEnvVar('ZES_ENABLE_SYSMAN', envConfig.zes_enable_sysman)"
              style="cursor: pointer;"
            ></div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">OLLAMA_HOST</div>
              <div class="setting-desc">Ollama 服务地址</div>
            </div>
            <div class="setting-value">{{ envConfig.ollama_host || '默认 (127.0.0.1:11434)' }}</div>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">OLLAMA_MODELS</div>
              <div class="setting-desc">模型存储目录</div>
            </div>
            <div class="setting-value">{{ envConfig.ollama_models || '默认目录' }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.toggle.disabled {
  opacity: 0.5;
  cursor: not-allowed !important;
}
</style>
