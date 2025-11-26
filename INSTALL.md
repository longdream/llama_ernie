# Llama ERNIE 环境安装指南

本文档记录了在 Windows 系统上从零开始安装和编译 Llama ERNIE 项目所需的所有环境和步骤。

## 系统要求

- **操作系统**: Windows 10/11 (64位)
- **内存**: 建议 16GB 以上 (运行 21B Q3 量化模型需要约 8GB)
- **磁盘空间**: 至少 20GB 可用空间

## 已安装的环境

### 1. Rust 工具链

- **版本**: rustc 1.91.1 (ed61e7d7e 2025-11-07)
- **Cargo**: cargo 1.91.1 (ea2d97820 2025-10-10)
- **安装方式**: 
  ```powershell
  winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements
  rustup default stable
  ```

### 2. Visual Studio 2022 Build Tools

- **版本**: 17.14.21
- **组件**:
  - Microsoft.VisualStudio.Workload.VCTools (C++ 桌面开发工具)
  - Microsoft.VisualStudio.Component.VC.Tools.x86.x64 (MSVC v143 编译器)
  - Microsoft.VisualStudio.Component.Windows11SDK.22621 (Windows 11 SDK)
- **安装方式**:
  ```powershell
  winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows11SDK.22621 --quiet --wait" --accept-source-agreements --accept-package-agreements
  ```

### 3. LLVM/Clang

- **版本**: 21.1.6
- **用途**: 提供 libclang.dll，用于 bindgen 生成 Rust FFI 绑定
- **安装路径**: `C:\Program Files\LLVM`
- **安装方式**:
  ```powershell
  winget install LLVM.LLVM --accept-source-agreements --accept-package-agreements
  ```

### 4. CMake

- **版本**: 4.2.0
- **用途**: 编译 llama.cpp C++ 库
- **安装路径**: `C:\Program Files\CMake`
- **安装方式**:
  ```powershell
  winget install Kitware.CMake --accept-source-agreements --accept-package-agreements
  ```

### 5. Git

- **用途**: 克隆依赖库和子模块
- **安装路径**: `C:\Program Files\Git`

## 模型文件

- **模型名称**: ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf
- **模型路径**: `C:\Users\devcloud\Downloads\exe\ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf`
- **模型大小**: 约 8GB (Q3 量化)
- **内存需求**: 约 8GB RAM

## 编译步骤

### 1. 克隆依赖库

```powershell
cd C:\llama_ernie
git clone https://github.com/utilityai/llama-cpp-rs.git vendor/llama-cpp-rs
```

### 2. 初始化子模块

```powershell
cd C:\llama_ernie\vendor\llama-cpp-rs
git submodule update --init --recursive
```

### 3. 编译项目

需要在 Visual Studio 开发者环境中编译，并设置 LIBCLANG_PATH：

```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
set "LIBCLANG_PATH=C:\Program Files\LLVM\bin"
set "PATH=C:\Program Files\CMake\bin;%PATH%"
cd /d C:\llama_ernie
cargo build --release
```

或者使用 PowerShell 一行命令：

```powershell
cmd /c "call `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat`" x64 > nul 2>&1 & set `"LIBCLANG_PATH=C:\Program Files\LLVM\bin`" & set `"PATH=C:\Program Files\CMake\bin;%PATH%`" & cd /d C:\llama_ernie & cargo build --release"
```

### 4. 复制可执行文件

```powershell
copy C:\llama_ernie\target\release\llama_ernie_server.exe C:\llama_ernie\llama_ernie_server.exe
```

## 配置文件

配置文件位于 `C:\llama_ernie\config.toml`，主要配置项：

```toml
[server]
host = "0.0.0.0"
port = 8766

[model]
path = "C:/Users/devcloud/Downloads/exe/ERNIE-4.5-21B-A3B-PT-Q3_K_S.gguf"
name = "ernie-21b"

[inference]
n_ctx = 16384      # 最大上下文长度
n_threads = 10     # CPU 线程数（建议设为物理核心数）
n_gpu_layers = 0   # 纯 CPU 推理设为 0
use_mmap = true    # 使用内存映射
n_batch = 512      # 批处理大小
```

## 运行服务

```powershell
cd C:\llama_ernie
.\llama_ernie_server.exe
```

或使用提供的批处理文件：

```powershell
.\start.bat
```

## 测试服务

```powershell
# 健康检查
curl http://localhost:8766/health

# 模型列表
curl http://localhost:8766/v1/models

# 聊天测试
curl http://localhost:8766/v1/chat/completions -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "你好"}], "temperature": 0.7, "max_tokens": 512}'
```

## 环境变量汇总

| 环境变量 | 值 | 用途 |
|---------|-----|------|
| LIBCLANG_PATH | C:\Program Files\LLVM\bin | bindgen 查找 libclang.dll |
| PATH | 需包含 CMake bin 目录 | cmake 命令可用 |
| VCINSTALLDIR | 由 vcvarsall.bat 设置 | MSVC 编译器路径 |

## 常见问题

### 1. 找不到 link.exe

确保已安装 Visual Studio Build Tools 并包含 C++ 工具组件。

### 2. 找不到 libclang.dll

设置 `LIBCLANG_PATH` 环境变量指向 LLVM bin 目录。

### 3. 找不到 cmake

确保 CMake 已安装并添加到 PATH。

### 4. 找不到 llama.h

确保已初始化 git 子模块：`git submodule update --init --recursive`

## 版本信息

- **编译日期**: 2025-11-26
- **Rust**: 1.91.1
- **LLVM**: 21.1.6
- **CMake**: 4.2.0
- **Visual Studio Build Tools**: 17.14.21

