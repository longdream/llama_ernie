use serde::{Deserialize, Serialize};
use crate::cmd;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuInfo {
    pub name: String,
    pub adapter_ram: u64,
    pub driver_version: String,
    pub is_intel_arc: bool,
    pub vulkan_supported: bool,
}

pub fn detect_gpu() -> Result<Vec<GpuInfo>, String> {
    // Use PowerShell to get GPU info (avoids COM threading issues)
    let output = cmd::powershell(&[
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json -Compress"
    ]).map_err(|e| format!("Failed to run PowerShell: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    
    let mut gpus = Vec::new();

    // Parse JSON output
    if let Ok(json) = serde_json::from_str::<serde_json::Value>(&stdout) {
        let items = if json.is_array() {
            json.as_array().unwrap().clone()
        } else {
            vec![json]
        };

        for item in items {
            let name = item.get("Name")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            
            // Skip virtual/remote display adapters
            if name.contains("Remote") || name.contains("Virtual") || name.contains("Basic") || name.is_empty() {
                continue;
            }

            let adapter_ram = item.get("AdapterRAM")
                .and_then(|v| v.as_u64())
                .unwrap_or(0);
            
            let driver_version = item.get("DriverVersion")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();

            let is_intel_arc = name.contains("Intel") && (name.contains("Arc") || name.contains("Graphics"));
            let vulkan_supported = is_intel_arc || name.contains("NVIDIA") || name.contains("AMD") || name.contains("Radeon");

            gpus.push(GpuInfo {
                name,
                adapter_ram,
                driver_version,
                is_intel_arc,
                vulkan_supported,
            });
        }
    }

    Ok(gpus)
}

pub fn get_intel_gpu() -> Option<GpuInfo> {
    detect_gpu().ok()?.into_iter().find(|g| g.is_intel_arc)
}
