mod cmd;
mod config;
mod gpu;
mod ollama;

use config::{EnvConfig, SystemInfo};
use gpu::GpuInfo;
use ollama::{OllamaModel, OllamaStatus, OllamaVersion, TestResult, PreloadResult, ImportResult};

// ============ GPU Commands ============

#[tauri::command]
async fn detect_gpu() -> Result<Vec<GpuInfo>, String> {
    tokio::task::spawn_blocking(|| gpu::detect_gpu())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn get_intel_gpu() -> Option<GpuInfo> {
    tokio::task::spawn_blocking(|| gpu::get_intel_gpu())
        .await
        .ok()?
}

// ============ Ollama Commands ============

#[tauri::command]
async fn check_ollama_installed() -> OllamaVersion {
    tokio::task::spawn_blocking(|| ollama::check_ollama_installed())
        .await
        .unwrap_or(OllamaVersion { installed: false, version: String::new() })
}

#[tauri::command]
async fn list_ollama_models() -> Result<Vec<OllamaModel>, String> {
    tokio::task::spawn_blocking(|| ollama::get_models())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn get_running_models() -> Result<Vec<OllamaStatus>, String> {
    tokio::task::spawn_blocking(|| ollama::get_running_models())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn pull_ollama_model(model_name: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || ollama::pull_model(&model_name))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn delete_ollama_model(model_name: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || ollama::delete_model(&model_name))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn run_speed_test(model_name: String, prompt: String, enable_think: bool) -> Result<TestResult, String> {
    tokio::task::spawn_blocking(move || ollama::run_model_test(&model_name, &prompt, enable_think))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn preload_model(model_name: String, keep_alive: String) -> Result<PreloadResult, String> {
    tokio::task::spawn_blocking(move || ollama::preload_model(&model_name, &keep_alive))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn set_model_keep_alive(model_name: String, duration: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || ollama::set_keep_alive(&model_name, &duration))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn is_model_loaded(model_name: String) -> bool {
    tokio::task::spawn_blocking(move || ollama::is_model_loaded(&model_name))
        .await
        .unwrap_or(false)
}

#[tauri::command]
async fn unload_model(model_name: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || ollama::unload_model(&model_name))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn import_gguf_model(gguf_path: String, model_name: String) -> Result<ImportResult, String> {
    tokio::task::spawn_blocking(move || ollama::import_gguf_model(&gguf_path, &model_name))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

// ============ Config Commands ============

#[tauri::command]
async fn get_env_config() -> EnvConfig {
    tokio::task::spawn_blocking(|| config::get_env_config())
        .await
        .unwrap_or(EnvConfig {
            ollama_vulkan: None,
            zes_enable_sysman: None,
            ollama_host: None,
            ollama_models: None,
        })
}

#[tauri::command]
async fn set_env_variable(name: String, value: String, system_wide: bool) -> Result<(), String> {
    tokio::task::spawn_blocking(move || config::set_env_variable(&name, &value, system_wide))
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn configure_ollama_vulkan() -> Result<String, String> {
    tokio::task::spawn_blocking(|| config::configure_ollama_vulkan())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn configure_ipex_llm() -> Result<String, String> {
    tokio::task::spawn_blocking(|| config::configure_ipex_llm())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn restart_ollama_service() -> Result<String, String> {
    tokio::task::spawn_blocking(|| config::restart_ollama_service())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String> {
    tokio::task::spawn_blocking(|| config::get_system_info())
        .await
        .map_err(|e| format!("Task failed: {}", e))?
}

// ============ App Entry ============

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            // GPU
            detect_gpu,
            get_intel_gpu,
            // Ollama
            check_ollama_installed,
            list_ollama_models,
            get_running_models,
            pull_ollama_model,
            delete_ollama_model,
            run_speed_test,
            // Preload & Keep Alive
            preload_model,
            set_model_keep_alive,
            is_model_loaded,
            unload_model,
            // Import GGUF
            import_gguf_model,
            // Config
            get_env_config,
            set_env_variable,
            configure_ollama_vulkan,
            configure_ipex_llm,
            restart_ollama_service,
            get_system_info,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
