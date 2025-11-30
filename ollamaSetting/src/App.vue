<script setup lang="ts">
import { ref } from 'vue';
import SystemInfo from './components/SystemInfo.vue';
import GpuConfig from './components/GpuConfig.vue';
import ModelManager from './components/ModelManager.vue';
import PerformanceMonitor from './components/PerformanceMonitor.vue';

const currentPage = ref<'system' | 'gpu' | 'models' | 'monitor'>('system');

const navItems = [
  { id: 'system', label: '系统信息', icon: 'computer' },
  { id: 'gpu', label: 'GPU 配置', icon: 'gpu' },
  { id: 'models', label: '模型管理', icon: 'model' },
  { id: 'monitor', label: '性能监控', icon: 'chart' },
] as const;

const pageTitle = {
  system: '系统信息',
  gpu: 'GPU 配置',
  models: '模型管理',
  monitor: '性能监控',
};

const pageDesc = {
  system: '查看系统硬件和 Ollama 运行状态',
  gpu: '配置 Intel GPU 加速选项',
  models: '下载和管理 AI 模型',
  monitor: '测试和监控模型性能',
};
</script>

<template>
  <div id="app">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <h1>Ollama GPU</h1>
        <p>Intel Arc 配置工具</p>
      </div>
      
      <div class="nav-section">
        <div class="nav-section-title">设置</div>
        <nav>
          <div
            v-for="item in navItems"
            :key="item.id"
            class="nav-item"
            :class="{ active: currentPage === item.id }"
            @click="currentPage = item.id"
          >
            <!-- Computer Icon -->
            <svg v-if="item.icon === 'computer'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            
            <!-- GPU Icon -->
            <svg v-if="item.icon === 'gpu'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
              <rect x="8" y="8" width="8" height="8" rx="1"/>
              <line x1="2" y1="9" x2="4" y2="9"/>
              <line x1="2" y1="15" x2="4" y2="15"/>
              <line x1="20" y1="9" x2="22" y2="9"/>
              <line x1="20" y1="15" x2="22" y2="15"/>
            </svg>
            
            <!-- Model Icon -->
            <svg v-if="item.icon === 'model'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
              <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
            
            <!-- Chart Icon -->
            <svg v-if="item.icon === 'chart'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            
            <span>{{ item.label }}</span>
          </div>
        </nav>
      </div>

      <div style="flex: 1;"></div>
      
      <div style="padding: 16px 20px; border-top: 1px solid var(--color-border);">
        <div style="font-size: 12px; color: var(--color-text-muted);">
          版本 0.1.0
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <header class="header">
        <div>
          <h2>{{ pageTitle[currentPage] }}</h2>
          <p style="font-size: 13px; color: var(--color-text-muted); margin-top: 2px;">
            {{ pageDesc[currentPage] }}
          </p>
        </div>
        <div class="header-actions">
          <span class="badge badge-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            在线
          </span>
        </div>
      </header>

      <div class="content">
        <SystemInfo v-if="currentPage === 'system'" />
        <GpuConfig v-if="currentPage === 'gpu'" />
        <ModelManager v-if="currentPage === 'models'" />
        <PerformanceMonitor v-if="currentPage === 'monitor'" />
      </div>
    </main>
  </div>
</template>
