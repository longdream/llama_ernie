use serde::{Deserialize, Serialize};
use winreg::enums::*;
use winreg::RegKey;
use crate::cmd;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvConfig {
    pub ollama_vulkan: Option<String>,
    pub zes_enable_sysman: Option<String>,
    pub ollama_host: Option<String>,
    pub ollama_models: Option<String>,
}

pub fn get_env_config() -> EnvConfig {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let env_key = hkcu.open_subkey("Environment").ok();

    let get_value = |key: &Option<RegKey>, name: &str| -> Option<String> {
        key.as_ref()
            .and_then(|k| k.get_value::<String, _>(name).ok())
    };

    EnvConfig {
        ollama_vulkan: get_value(&env_key, "OLLAMA_VULKAN"),
        zes_enable_sysman: get_value(&env_key, "ZES_ENABLE_SYSMAN"),
        ollama_host: get_value(&env_key, "OLLAMA_HOST"),
        ollama_models: get_value(&env_key, "OLLAMA_MODELS"),
    }
}

pub fn set_env_variable(name: &str, value: &str, system_wide: bool) -> Result<(), String> {
    if system_wide {
        // System-wide requires admin privileges, use setx command
        let output = cmd::run("setx", &[name, value, "/M"])
            .map_err(|e| format!("Failed to run setx: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!(
                "setx failed (may need admin privileges): {}",
                stderr
            ));
        }
    } else {
        // User-level via registry
        let hkcu = RegKey::predef(HKEY_CURRENT_USER);
        let (env_key, _) = hkcu
            .create_subkey("Environment")
            .map_err(|e| format!("Failed to open Environment key: {}", e))?;

        env_key
            .set_value(name, &value)
            .map_err(|e| format!("Failed to set {}: {}", name, e))?;

        // Broadcast WM_SETTINGCHANGE to notify other processes
        broadcast_env_change();
    }

    Ok(())
}

#[allow(dead_code)]
pub fn delete_env_variable(name: &str, system_wide: bool) -> Result<(), String> {
    if system_wide {
        // Use reg delete for system-wide
        let output = cmd::run("reg", &[
            "delete",
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment",
            "/v",
            name,
            "/f",
        ]).map_err(|e| format!("Failed to run reg delete: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("reg delete failed: {}", stderr));
        }
    } else {
        let hkcu = RegKey::predef(HKEY_CURRENT_USER);
        let env_key = hkcu
            .open_subkey_with_flags("Environment", KEY_WRITE)
            .map_err(|e| format!("Failed to open Environment key: {}", e))?;

        env_key
            .delete_value(name)
            .map_err(|e| format!("Failed to delete {}: {}", name, e))?;

        broadcast_env_change();
    }

    Ok(())
}

pub fn configure_ollama_vulkan() -> Result<String, String> {
    // Set OLLAMA_VULKAN=1 for Intel GPU support
    set_env_variable("OLLAMA_VULKAN", "1", false)?;

    // Set ZES_ENABLE_SYSMAN=1 for system management
    set_env_variable("ZES_ENABLE_SYSMAN", "1", false)?;

    Ok("Ollama Vulkan configuration applied. Please restart Ollama for changes to take effect.".to_string())
}

pub fn configure_ipex_llm() -> Result<String, String> {
    // Set OLLAMA_NUM_GPU=999 to use all available GPU layers
    set_env_variable("OLLAMA_NUM_GPU", "999", false)?;
    
    // Set no_proxy for local connections
    set_env_variable("no_proxy", "localhost,127.0.0.1", false)?;
    
    // Set ZES_ENABLE_SYSMAN=1 for Intel GPU system management
    set_env_variable("ZES_ENABLE_SYSMAN", "1", false)?;
    
    // Set SYCL_CACHE_PERSISTENT=1 for better performance
    set_env_variable("SYCL_CACHE_PERSISTENT", "1", false)?;
    
    // Set OLLAMA_INTEL_GPU=1 for Intel GPU support
    set_env_variable("OLLAMA_INTEL_GPU", "1", false)?;

    Ok("IPEX-LLM 优化配置已应用，请重启 Ollama 使配置生效".to_string())
}

pub fn restart_ollama_service() -> Result<String, String> {
    // Stop any running ollama processes (hidden)
    let _ = cmd::run("taskkill", &["/F", "/IM", "ollama.exe"]);
    let _ = cmd::run("taskkill", &["/F", "/IM", "ollama_llama_server.exe"]);

    // Wait a moment
    std::thread::sleep(std::time::Duration::from_secs(2));

    // Start ollama serve in background using PowerShell (hidden)
    let _ = cmd::powershell(&[
        "-NoProfile",
        "-Command",
        "Start-Process ollama -ArgumentList 'serve' -WindowStyle Hidden"
    ]);

    Ok("Ollama service restarted".to_string())
}

fn broadcast_env_change() {
    // Use PowerShell to broadcast environment change (hidden)
    let _ = cmd::powershell(&[
        "-NoProfile",
        "-Command",
        "[Environment]::SetEnvironmentVariable('__DUMMY__', $null, 'User')"
    ]);
}

pub fn get_system_info() -> Result<SystemInfo, String> {
    // Get CPU name using PowerShell with Get-CimInstance
    let cpu_output = cmd::powershell(&[
        "-NoProfile",
        "-Command",
        "(Get-CimInstance Win32_Processor).Name"
    ]);

    let cpu_name = cpu_output
        .ok()
        .map(|o| {
            String::from_utf8_lossy(&o.stdout)
                .trim()
                .to_string()
        })
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "Unknown".to_string());

    // Get total memory using PowerShell
    let mem_output = cmd::powershell(&[
        "-NoProfile",
        "-Command",
        "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"
    ]);

    let total_memory = mem_output
        .ok()
        .and_then(|o| {
            String::from_utf8_lossy(&o.stdout)
                .trim()
                .parse::<u64>()
                .ok()
        })
        .unwrap_or(0);

    Ok(SystemInfo {
        cpu_name,
        total_memory,
        os_version: "Windows".to_string(),
    })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub cpu_name: String,
    pub total_memory: u64,
    pub os_version: String,
}
