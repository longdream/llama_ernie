# OllamaSetting - Ollama GPU 配置工具

一个基于 Tauri + Vue 3 + TypeScript 开发的 Intel Arc GPU 配置工具，用于管理 Ollama 的 GPU 设置。

## 环境要求

在编译和运行之前，请确保已安装以下环境：

- **Node.js** (v18+)
- **pnpm** (包管理器)
- **Rust** (最新稳定版)
- **Visual Studio Build Tools** (Windows 需要 C++ 编译环境)

### 安装 pnpm

```bash
npm install -g pnpm
```

### 安装 Rust

访问 https://rustup.rs/ 下载安装 Rust。

## 开发模式

### 1. 安装依赖

```bash
cd ollamaSetting
pnpm install
```

### 2. 启动开发服务器

```bash
pnpm tauri dev
```

这将同时启动：
- Vite 开发服务器 (http://localhost:1420)
- Tauri 桌面应用窗口

## 生产构建

### 构建安装包

```bash
pnpm tauri build
```

构建完成后，安装包将位于：

```
src-tauri/target/release/bundle/
├── msi/          # Windows MSI 安装包
└── nsis/         # Windows NSIS 安装包
```

## 项目结构

```
ollamaSetting/
├── src/                    # Vue 前端源码
├── src-tauri/              # Tauri/Rust 后端源码
│   ├── src/
│   │   ├── main.rs         # 应用入口
│   │   ├── lib.rs          # 库入口
│   │   ├── cmd.rs          # 命令模块
│   │   ├── config.rs       # 配置模块
│   │   ├── gpu.rs          # GPU 相关功能
│   │   └── ollama.rs       # Ollama 相关功能
│   ├── Cargo.toml          # Rust 依赖配置
│   └── tauri.conf.json     # Tauri 配置
├── package.json            # Node.js 依赖配置
└── vite.config.ts          # Vite 配置
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `pnpm install` | 安装前端依赖 |
| `pnpm tauri dev` | 启动开发模式 |
| `pnpm tauri build` | 构建生产版本 |
| `pnpm dev` | 仅启动前端开发服务器 |
| `pnpm build` | 仅构建前端 |

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite + Tailwind CSS + ECharts
- **后端**: Rust + Tauri 2.0
- **UI**: Tailwind CSS v4
