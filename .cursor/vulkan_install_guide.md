# Vulkan SDK 安装与检测指南

## 现状检查
- 系统已存在 `vulkaninfo`（位于 `C:\Windows\System32\vulkaninfo.exe`），说明运行时可用。
- `VULKAN_SDK` 环境变量未设置；`C:\VulkanSDK\...` 未找到已安装的 SDK。

## 需要安装完整 Vulkan SDK 时
1. 访问 https://vulkan.lunarg.com/sdk/home 下载 Windows 版 SDK（建议与 `build_vulkan.bat` 中的版本一致，示例 `1.4.328.1`）。
2. 安装时勾选：
   - Vulkan Runtime
   - 开发头文件与库
   - GLSLang / ShaderC 等工具
3. 安装完成后确认环境变量：
   - `VULKAN_SDK` 应指向类似 `C:\VulkanSDK\1.4.328.1`
   - `PATH` 中应包含 `%VULKAN_SDK%\Bin`

## 自动检测逻辑（已写入 `build_vulkan.bat`）
- 优先使用已设置的 `VULKAN_SDK`
- 否则尝试检测 `C:\VulkanSDK\1.4.328.1`
- 否则遍历 `C:\VulkanSDK\` 下最新版本目录
- 若仍未找到，则继续使用系统 Vulkan 运行时（可编译，但缺少 SDK 头文件时可能失败）

## 安装后验证
```powershell
vulkaninfo | Select-String "Vulkan Instance Version"
```
期望能输出版本号且无错误。

## 如果仍然找不到 SDK
- 确认安装路径是否在 `C:\VulkanSDK`
- 手动设置环境变量（示例）：
```powershell
$env:VULKAN_SDK="C:\VulkanSDK\1.4.328.1"
$env:PATH="$env:VULKAN_SDK\Bin;$env:PATH"
```
可写入系统环境变量以长期生效。

