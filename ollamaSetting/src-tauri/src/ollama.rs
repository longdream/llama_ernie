use regex::Regex;
use serde::{Deserialize, Serialize};
use std::path::Path;
use crate::cmd;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaVersion {
    pub installed: bool,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaModel {
    pub name: String,
    pub id: String,
    pub size: String,
    pub modified: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaStatus {
    pub name: String,
    pub id: String,
    pub size: String,
    pub processor: String,
    pub context: String,
    pub until: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestResult {
    pub model: String,
    pub total_duration: String,
    pub load_duration: String,
    pub prompt_eval_count: u32,
    pub prompt_eval_rate: f64,
    pub eval_count: u32,
    pub eval_rate: f64,
    pub processor: String,
    pub timestamp: String,
    pub response: String,
}

/// Find ollama executable path
fn get_ollama_path() -> Option<String> {
    // Common installation paths for Ollama on Windows
    let possible_paths = [
        // User local install (most common)
        format!("{}\\AppData\\Local\\Programs\\Ollama\\ollama.exe", std::env::var("USERPROFILE").unwrap_or_default()),
        // Program Files
        "C:\\Program Files\\Ollama\\ollama.exe".to_string(),
        // ProgramData
        "C:\\ProgramData\\Ollama\\ollama.exe".to_string(),
        // Just try PATH
        "ollama".to_string(),
    ];

    for path in &possible_paths {
        if path == "ollama" {
            // Try running from PATH
            if let Ok(output) = cmd::run("ollama", &["--version"]) {
                if output.status.success() || !output.stdout.is_empty() || !output.stderr.is_empty() {
                    return Some("ollama".to_string());
                }
            }
        } else if Path::new(path).exists() {
            return Some(path.clone());
        }
    }

    None
}

pub fn check_ollama_installed() -> OllamaVersion {
    let ollama_path = match get_ollama_path() {
        Some(path) => path,
        None => return OllamaVersion { installed: false, version: String::new() },
    };

    let output = cmd::run(&ollama_path, &["--version"]);

    match output {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            let stderr = String::from_utf8_lossy(&out.stderr);
            let combined = format!("{}{}", stdout, stderr);

            let version_re = Regex::new(r"ollama version is (\S+)").unwrap();
            if let Some(caps) = version_re.captures(&combined) {
                OllamaVersion {
                    installed: true,
                    version: caps.get(1).map_or("unknown".to_string(), |m| m.as_str().to_string()),
                }
            } else if combined.contains("ollama") || combined.contains("version") {
                // Try to extract version number
                let ver_re = Regex::new(r"(\d+\.\d+\.\d+)").unwrap();
                let version = ver_re.captures(&combined)
                    .and_then(|c| c.get(1))
                    .map(|m| m.as_str().to_string())
                    .unwrap_or_else(|| combined.trim().to_string());
                OllamaVersion {
                    installed: true,
                    version,
                }
            } else {
                OllamaVersion {
                    installed: false,
                    version: String::new(),
                }
            }
        }
        Err(_) => OllamaVersion {
            installed: false,
            version: String::new(),
        },
    }
}

pub fn get_models() -> Result<Vec<OllamaModel>, String> {
    let ollama_path = get_ollama_path().ok_or("Ollama not found")?;
    
    let output = cmd::run(&ollama_path, &["list"])
        .map_err(|e| format!("Failed to run ollama list: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut models = Vec::new();

    // ollama list 输出格式:
    // NAME                                  ID              SIZE      MODIFIED      
    // ernie-4-5-21b-a3b-pt:latest           0d4a50d850a7    9.5 GB    8 minutes ago
    // 
    // 分词后: [0]=name [1]=id [2]=9.5 [3]=GB [4..]=8 minutes ago

    for line in stdout.lines().skip(1) {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        
        let parts: Vec<&str> = line.split_whitespace().collect();
        // 至少需要: NAME, ID, SIZE(数字), SIZE(单位), MODIFIED(至少一个词)
        if parts.len() >= 5 {
            models.push(OllamaModel {
                name: parts[0].to_string(),
                id: parts[1].to_string(),
                size: format!("{} {}", parts[2], parts[3]), // "9.5 GB"
                modified: parts[4..].join(" "), // "8 minutes ago"
            });
        }
    }

    Ok(models)
}

pub fn get_running_models() -> Result<Vec<OllamaStatus>, String> {
    let ollama_path = get_ollama_path().ok_or("Ollama not found")?;
    
    let output = cmd::run(&ollama_path, &["ps"])
        .map_err(|e| format!("Failed to run ollama ps: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut models = Vec::new();

    // ollama ps 输出格式:
    // NAME             ID              SIZE     PROCESSOR         CONTEXT    UNTIL
    // qwen3:30b-a3b    ad815644918f    19 GB    4%/96% CPU/GPU    4096       3 minutes from now
    // 
    // 分词后:
    // [0]=qwen3:30b-a3b [1]=ad815644918f [2]=19 [3]=GB [4]=4%/96% [5]=CPU/GPU [6]=4096 [7..]=3 minutes from now
    
    for line in stdout.lines().skip(1) {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 7 {
            continue;
        }
        
        let name = parts[0].to_string();
        let id = parts[1].to_string();
        
        // 找到 CONTEXT 字段的位置（纯数字，不含 % 或字母，通常是 4096 这样的值）
        let mut context_idx = 0;
        for (i, part) in parts.iter().enumerate().skip(2) {
            // CONTEXT 是一个纯数字（可能很大，如 4096, 8192 等）
            if part.parse::<u64>().is_ok() && !part.contains('%') && part.len() >= 3 {
                context_idx = i;
                break;
            }
        }
        
        if context_idx >= 4 {
            // SIZE 是 parts[2] 和 parts[3]，如 "19 GB"
            let size = format!("{} {}", parts[2], parts[3]);
            // PROCESSOR 是从 parts[4] 到 context_idx-1
            let processor = parts[4..context_idx].join(" ");
            let context = parts[context_idx].to_string();
            let until = parts[context_idx+1..].join(" ");
            
            models.push(OllamaStatus {
                name,
                id,
                size,
                processor,
                context,
                until,
            });
        }
    }

    Ok(models)
}

pub fn pull_model(name: &str) -> Result<String, String> {
    let ollama_path = get_ollama_path().ok_or("Ollama not found")?;
    
    let output = cmd::run(&ollama_path, &["pull", name])
        .map_err(|e| format!("Failed to pull model: {}", e))?;

    if output.status.success() {
        Ok(format!("Successfully pulled {}", name))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to pull {}: {}", name, stderr))
    }
}

pub fn delete_model(name: &str) -> Result<String, String> {
    let ollama_path = get_ollama_path().ok_or("Ollama not found")?;
    
    let output = cmd::run(&ollama_path, &["rm", name])
        .map_err(|e| format!("Failed to delete model: {}", e))?;

    if output.status.success() {
        Ok(format!("Successfully deleted {}", name))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Failed to delete {}: {}", name, stderr))
    }
}

fn get_current_processor(model_name: &str) -> String {
    // Try to get processor info from ollama ps
    if let Ok(models) = get_running_models() {
        for model in models {
            if model.name.starts_with(model_name) || model_name.starts_with(&model.name) {
                return model.processor;
            }
        }
    }
    // Default to checking environment variable
    if std::env::var("OLLAMA_VULKAN").unwrap_or_default() == "1" {
        "GPU (Vulkan)".to_string()
    } else {
        "CPU".to_string()
    }
}

fn format_duration(seconds: f64) -> String {
    if seconds < 1.0 {
        format!("{:.0}ms", seconds * 1000.0)
    } else if seconds < 60.0 {
        format!("{:.2}s", seconds)
    } else {
        let mins = (seconds / 60.0).floor();
        let secs = seconds % 60.0;
        format!("{:.0}m {:.2}s", mins, secs)
    }
}

fn get_timestamp() -> String {
    let now = std::time::SystemTime::now();
    let duration = now.duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    let secs = duration.as_secs();
    
    // Adjust for China timezone (UTC+8)
    let china_secs = secs + 8 * 3600;
    let hours = (china_secs % 86400) / 3600;
    let minutes = (china_secs % 3600) / 60;
    let seconds = china_secs % 60;
    
    format!("{:02}:{:02}:{:02}", hours, minutes, seconds)
}

pub fn run_model_test(name: &str, prompt: &str, enable_think: bool) -> Result<TestResult, String> {
    // 使用 Ollama API 进行测试，避免 ollama run 命令阻塞
    let start_time = std::time::Instant::now();
    
    // 根据 think 开关构建最终 prompt
    // Qwen3 等模型支持 /think 和 /no_think 指令
    let final_prompt = if enable_think {
        prompt.to_string()
    } else {
        format!("/no_think {}", prompt)
    };
    
    // 构建请求 JSON
    let json_body = format!(
        r#"{{"model":"{}","prompt":"{}","stream":false}}"#,
        name, 
        final_prompt.replace("\"", "\\\"").replace("\n", "\\n")
    );
    
    let output = cmd::hidden_command("curl")
        .args(&[
            "-s",
            "-X", "POST",
            "http://localhost:11434/api/generate",
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .output()
        .map_err(|e| format!("执行 curl 命令失败: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    let total_elapsed = start_time.elapsed();

    // 解析 JSON 响应
    // 响应格式: {"model":"...","response":"...","done":true,"total_duration":...,"load_duration":...,"prompt_eval_count":...,"prompt_eval_duration":...,"eval_count":...,"eval_duration":...}
    
    // 提取各个字段
    let total_duration_ns = parse_json_u64(&stdout, "total_duration");
    let load_duration_ns = parse_json_u64(&stdout, "load_duration");
    let prompt_eval_count = parse_json_u32(&stdout, "prompt_eval_count");
    let prompt_eval_duration_ns = parse_json_u64(&stdout, "prompt_eval_duration");
    let eval_count = parse_json_u32(&stdout, "eval_count");
    let eval_duration_ns = parse_json_u64(&stdout, "eval_duration");
    
    // 计算速率 (tokens/s)
    let prompt_eval_rate = if prompt_eval_duration_ns > 0 {
        (prompt_eval_count as f64) / (prompt_eval_duration_ns as f64 / 1_000_000_000.0)
    } else {
        0.0
    };
    
    let eval_rate = if eval_duration_ns > 0 {
        (eval_count as f64) / (eval_duration_ns as f64 / 1_000_000_000.0)
    } else {
        0.0
    };
    
    // 提取响应文本
    let response = parse_json_string(&stdout, "response");

    // Get processor info
    let processor = get_current_processor(name);
    
    // Get current timestamp
    let timestamp = get_timestamp();

    // 如果所有值都是0，说明解析失败，返回详细错误信息
    if eval_rate == 0.0 && prompt_eval_rate == 0.0 && eval_count == 0 {
        let stdout_display = if stdout.is_empty() { "(空)".to_string() } else { stdout.to_string() };
        let stderr_display = if stderr.is_empty() { "(空)".to_string() } else { stderr.to_string() };
        return Err(format!(
            "解析测试结果失败，未能获取性能数据。\n\n可能原因:\n1. Ollama 服务未运行\n2. 模型未正确加载\n3. API 请求失败\n\n原始输出:\nSTDOUT: {}\nSTDERR: {}",
            stdout_display, stderr_display
        ));
    }

    Ok(TestResult {
        model: name.to_string(),
        total_duration: format_duration(total_duration_ns as f64 / 1_000_000_000.0),
        load_duration: format_duration(load_duration_ns as f64 / 1_000_000_000.0),
        prompt_eval_count,
        prompt_eval_rate,
        eval_count,
        eval_rate,
        processor,
        timestamp,
        response,
    })
}

// JSON 解析辅助函数
fn parse_json_u64(json: &str, key: &str) -> u64 {
    let pattern = format!(r#""{}"\s*:\s*(\d+)"#, key);
    let re = Regex::new(&pattern).unwrap();
    re.captures(json)
        .and_then(|c| c.get(1))
        .map_or(0, |m| m.as_str().parse().unwrap_or(0))
}

fn parse_json_u32(json: &str, key: &str) -> u32 {
    let pattern = format!(r#""{}"\s*:\s*(\d+)"#, key);
    let re = Regex::new(&pattern).unwrap();
    re.captures(json)
        .and_then(|c| c.get(1))
        .map_or(0, |m| m.as_str().parse().unwrap_or(0))
}

fn parse_json_string(json: &str, key: &str) -> String {
    // 简单的 JSON 字符串提取，处理转义字符
    let pattern = format!(r#""{}"\s*:\s*"((?:[^"\\]|\\.)*)""#, key);
    let re = Regex::new(&pattern).unwrap();
    re.captures(json)
        .and_then(|c| c.get(1))
        .map(|m| {
            m.as_str()
                .replace("\\n", "\n")
                .replace("\\\"", "\"")
                .replace("\\\\", "\\")
        })
        .unwrap_or_default()
}

fn parse_duration(text: &str, pattern: &str) -> f64 {
    let re = Regex::new(pattern).unwrap();
    if let Some(caps) = re.captures(text) {
        let value: f64 = caps.get(1).map_or(0.0, |m| m.as_str().parse().unwrap_or(0.0));
        let unit = caps.get(2).map_or("s", |m| m.as_str());
        match unit {
            "ms" => value / 1000.0,
            "m" => value * 60.0,
            "h" => value * 3600.0,
            _ => value,
        }
    } else {
        0.0
    }
}

fn parse_f64(text: &str, pattern: &str) -> f64 {
    let re = Regex::new(pattern).unwrap();
    re.captures(text)
        .and_then(|c| c.get(1))
        .map_or(0.0, |m| m.as_str().parse().unwrap_or(0.0))
}

fn parse_u32(text: &str, pattern: &str) -> u32 {
    let re = Regex::new(pattern).unwrap();
    re.captures(text)
        .and_then(|c| c.get(1))
        .map_or(0, |m| m.as_str().parse().unwrap_or(0))
}

// ==================== 预加载功能 ====================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PreloadResult {
    pub success: bool,
    pub model: String,
    pub message: String,
    pub load_duration: String,
}

/// 停止所有正在运行的模型（确保单模型运行）
pub fn stop_all_running_models() -> Result<Vec<String>, String> {
    let running = get_running_models()?;
    let mut stopped = Vec::new();
    
    for model in running {
        // 使用 keep_alive: "0" 来卸载模型
        if let Ok(_) = set_keep_alive(&model.name, "0") {
            stopped.push(model.name.clone());
        }
    }
    
    // 等待足够时间确保模型完全卸载
    if !stopped.is_empty() {
        // 等待 2 秒，确保 Ollama 完成卸载
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        // 再次检查是否还有运行中的模型
        if let Ok(still_running) = get_running_models() {
            if !still_running.is_empty() {
                // 如果还有模型在运行，再等待一下
                std::thread::sleep(std::time::Duration::from_secs(1));
            }
        }
    }
    
    Ok(stopped)
}

/// 预加载模型到内存（通过 API 发送一个简单请求来触发模型加载）
/// 支持多模型并行运行（需要设置环境变量 OLLAMA_MAX_LOADED_MODELS）
pub fn preload_model(name: &str, keep_alive: &str) -> Result<PreloadResult, String> {
    // 使用 Ollama API 发送一个简单请求来预热模型
    let start_time = std::time::Instant::now();
    
    // 构建 keep_alive 参数
    let keep_alive_value = if keep_alive.is_empty() || keep_alive == "default" {
        "5m".to_string()
    } else {
        keep_alive.to_string()
    };
    
    // 通过 API 发送请求来加载模型
    // 使用空 prompt 只触发模型加载，不生成内容
    let json_body = format!(
        r#"{{"model":"{}","prompt":"","stream":false,"keep_alive":"{}"}}"#,
        name, keep_alive_value
    );
    
    // 设置超时时间为 10 分钟（大模型加载可能需要较长时间）
    let output = cmd::hidden_command("curl")
        .args(&[
            "-s",
            "-X", "POST",
            "--max-time", "600",  // 10 分钟超时
            "--connect-timeout", "10",  // 连接超时 10 秒
            "http://localhost:11434/api/generate",
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .output()
        .map_err(|e| format!("Failed to preload model: {}", e))?;
    
    let elapsed = start_time.elapsed();
    let load_duration = format_duration(elapsed.as_secs_f64());
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    // 检查响应是否成功
    if output.status.success() && !stdout.contains("\"error\"") {
        Ok(PreloadResult {
            success: true,
            model: name.to_string(),
            message: format!("模型 {} 预加载成功", name),
            load_duration,
        })
    } else {
        let error_msg = if !stderr.is_empty() {
            stderr.to_string()
        } else if stdout.contains("error") {
            stdout.to_string()
        } else if stdout.is_empty() {
            "请求超时或 Ollama 服务未响应".to_string()
        } else {
            "未知错误".to_string()
        };
        Err(format!("预加载失败: {}", error_msg))
    }
}

/// 设置模型的 keep_alive 时间
/// duration: "5m", "1h", "24h", "-1"(永久), "0"(立即卸载)
pub fn set_keep_alive(name: &str, duration: &str) -> Result<String, String> {
    // Ollama 通过 API 设置 keep_alive
    // 发送一个带有 keep_alive 参数的请求
    let json_body = format!(r#"{{"model":"{}","prompt":"","stream":false,"keep_alive":"{}"}}"#, name, duration);
    
    let output = cmd::hidden_command("curl")
        .args(&[
            "-s",
            "-X", "POST",
            "http://localhost:11434/api/generate",
            "-H", "Content-Type: application/json",
            "-d", &json_body,
        ])
        .output()
        .map_err(|e| format!("Failed to set keep_alive: {}", e))?;
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    if output.status.success() && !stdout.contains("error") {
        Ok(format!("模型 {} 的 keep_alive 已设置为 {}", name, duration))
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("设置 keep_alive 失败: {} {}", stderr, stdout))
    }
}

/// 检查模型是否已加载到内存
pub fn is_model_loaded(name: &str) -> bool {
    if let Ok(models) = get_running_models() {
        for model in models {
            // 模型名可能带有 :latest 等标签
            if model.name.starts_with(name) || name.starts_with(&model.name.split(':').next().unwrap_or("")) {
                return true;
            }
        }
    }
    false
}

/// 卸载模型从内存
pub fn unload_model(name: &str) -> Result<String, String> {
    // 通过设置 keep_alive 为 0 来卸载模型
    set_keep_alive(name, "0")?;
    Ok(format!("模型 {} 已从内存中卸载", name))
}

// ==================== 导入 GGUF 功能 ====================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportResult {
    pub success: bool,
    pub model_name: String,
    pub message: String,
}

/// 导入本地 GGUF 模型文件
pub fn import_gguf_model(gguf_path: &str, model_name: &str) -> Result<ImportResult, String> {
    let ollama_path = get_ollama_path().ok_or("Ollama not found")?;
    
    // 验证文件存在
    if !Path::new(gguf_path).exists() {
        return Err(format!("GGUF 文件不存在: {}", gguf_path));
    }
    
    // 验证文件扩展名
    if !gguf_path.to_lowercase().ends_with(".gguf") {
        return Err("文件必须是 .gguf 格式".to_string());
    }
    
    // 验证模型名称
    if model_name.is_empty() {
        return Err("模型名称不能为空".to_string());
    }
    
    // 创建临时 Modelfile
    let temp_dir = std::env::temp_dir();
    let modelfile_path = temp_dir.join(format!("Modelfile_{}", model_name));
    
    // 使用绝对路径
    let abs_gguf_path = std::fs::canonicalize(gguf_path)
        .map_err(|e| format!("无法获取绝对路径: {}", e))?;
    
    // 写入 Modelfile 内容
    let modelfile_content = format!("FROM {}", abs_gguf_path.display());
    std::fs::write(&modelfile_path, &modelfile_content)
        .map_err(|e| format!("创建 Modelfile 失败: {}", e))?;
    
    // 执行 ollama create
    let output = cmd::run(&ollama_path, &[
        "create", 
        model_name, 
        "-f", 
        &modelfile_path.to_string_lossy()
    ]).map_err(|e| format!("执行 ollama create 失败: {}", e))?;
    
    // 清理临时文件
    let _ = std::fs::remove_file(&modelfile_path);
    
    if output.status.success() {
        Ok(ImportResult {
            success: true,
            model_name: model_name.to_string(),
            message: format!("模型 {} 导入成功", model_name),
        })
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        Err(format!("导入失败: {} {}", stderr, stdout))
    }
}