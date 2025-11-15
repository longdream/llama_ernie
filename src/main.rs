use axum::{
    extract::{Json, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{fs, path::{Path, PathBuf}, sync::Arc};
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tracing::{info, error};
use uuid::Uuid;
use chrono::Utc;
use anyhow::{Result, Context};

// llama.cpp bindings
use llama_cpp_2::context::params::LlamaContextParams;
use llama_cpp_2::llama_backend::LlamaBackend;
use llama_cpp_2::llama_batch::LlamaBatch;
use llama_cpp_2::model::params::LlamaModelParams;
use llama_cpp_2::model::{LlamaModel, AddBos};
use llama_cpp_2::sampling::LlamaSampler;

// ==================== 配置结构 ====================

#[derive(Debug, Deserialize, Clone)]
struct Config {
    server: ServerConfig,
    model: ModelConfig,
    inference: InferenceConfig,
    #[serde(default)]
    embedding: Option<EmbeddingConfig>,
}

#[derive(Debug, Deserialize, Clone)]
struct ServerConfig {
    host: String,
    port: u16,
}

#[derive(Debug, Deserialize, Clone)]
struct ModelConfig {
    path: String,
    name: String,
}

#[derive(Debug, Deserialize, Clone)]
struct InferenceConfig {
    n_ctx: u32,
    n_threads: u32,
    n_gpu_layers: u32,
    #[allow(dead_code)]
    use_mmap: bool,  // 保留配置字段以便将来使用
}

#[derive(Debug, Deserialize, Clone)]
struct EmbeddingConfig {
    model_path: String,
    model_name: String,
    #[allow(dead_code)]
    port: u16,  // 保留配置字段
    dimension: usize,
    #[serde(default = "default_embedding_n_ctx")]
    n_ctx: u32,
    #[serde(default = "default_embedding_n_threads")]
    n_threads: u32,
    #[serde(default = "default_embedding_n_batch")]
    n_batch: u32,
}

fn default_embedding_n_ctx() -> u32 { 8192 }
fn default_embedding_n_threads() -> u32 { 4 }
fn default_embedding_n_batch() -> u32 { 512 }

impl Config {
    fn load() -> Result<Self> {
        let config_path = "config.toml";
        if Path::new(config_path).exists() {
            let content = fs::read_to_string(config_path)?;
            let config: Config = toml::from_str(&content)?;
            Ok(config)
        } else {
            Ok(Self::default())
        }
    }
}

impl Default for Config {
    fn default() -> Self {
        Config {
            server: ServerConfig {
                host: "0.0.0.0".to_string(),
                port: 8766,
            },
            model: ModelConfig {
                path: "../models/ernie-4.5-0.3b-pt-q8_0.gguf".to_string(),
                name: "ernie-0.3b".to_string(),
            },
            inference: InferenceConfig {
                n_ctx: 8192,
                n_threads: 16,
                n_gpu_layers: 0,  // 纯CPU
                use_mmap: true,
            },
            embedding: Some(EmbeddingConfig {
                model_path: "../models/bge-m3-Q4_K_M.gguf".to_string(),
                model_name: "bge-m3".to_string(),
                port: 8767,
                dimension: 1024,
                n_ctx: 8192,
                n_threads: 4,
                n_batch: 512,
            }),
        }
    }
}

// ==================== 数据结构 ====================

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct ChatCompletionRequest {
    #[serde(default)]
    model: String,
    messages: Vec<Message>,
    #[serde(default)]
    temperature: Option<f32>,
    #[serde(default)]
    max_tokens: Option<i32>,
    #[serde(default)]
    #[allow(dead_code)]
    stream: bool,  // 保留字段，将来可能实现流式输出
    // OpenAI 标准参数
    #[serde(default)]
    top_p: Option<f32>,
    #[serde(default)]
    #[allow(dead_code)]
    n: Option<i32>,
    #[serde(default)]
    #[allow(dead_code)]
    stop: Option<Vec<String>>,
    #[serde(default)]
    #[allow(dead_code)]
    presence_penalty: Option<f32>,
    #[serde(default)]
    #[allow(dead_code)]
    frequency_penalty: Option<f32>,
}

#[derive(Debug, Serialize)]
struct ChatCompletionResponse {
    id: String,
    object: String,
    created: i64,
    model: String,
    choices: Vec<Choice>,
    usage: Usage,
}

#[derive(Debug, Serialize)]
struct Choice {
    index: usize,
    message: Message,
    finish_reason: String,
}

#[derive(Debug, Serialize)]
struct Usage {
    prompt_tokens: usize,
    completion_tokens: usize,
    total_tokens: usize,
}

#[derive(Debug, Serialize)]
struct ModelInfo {
    id: String,
    object: String,
    created: i64,
    owned_by: String,
}

#[derive(Debug, Serialize)]
struct ModelsResponse {
    object: String,
    data: Vec<ModelInfo>,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: String,
    model_loaded: bool,
    model_path: String,
    timestamp: String,
}

// ==================== Embedding 数据结构 ====================

#[derive(Debug, Deserialize)]
struct EmbeddingRequest {
    text: String,
    #[serde(default)]
    #[allow(dead_code)]
    model: String,  // 保留字段以便将来支持多模型
}

#[derive(Debug, Serialize)]
struct EmbeddingResponse {
    embedding: Vec<f32>,
    dimension: usize,
    model: String,
}

// ==================== 模型包装 ====================

struct ModelWrapper {
    model: LlamaModel,
    #[allow(dead_code)]
    model_path: String,  // 保留以便调试和日志记录
}

impl ModelWrapper {
    fn new(backend: &LlamaBackend, path: PathBuf, config: &InferenceConfig) -> Result<Self> {
        info!("正在加载模型: {:?}", path);
        
        let model_params = LlamaModelParams::default()
            .with_n_gpu_layers(config.n_gpu_layers);
        
        let model = LlamaModel::load_from_file(backend, path.clone(), &model_params)
            .context("模型加载失败")?;
        
        info!("✅ 模型加载成功");
        
        Ok(Self {
            model,
            model_path: path.to_string_lossy().to_string(),
        })
    }
    
    fn generate(&self, backend: &LlamaBackend, prompt: &str, max_tokens: i32, temperature: f32, n_threads: u32, n_ctx: u32) -> Result<(String, usize, usize)> {
        // 先tokenize prompt以获取实际长度
        let tokens = self.model.str_to_token(prompt, AddBos::Always)
            .context("Tokenize失败")?;
        
        let prompt_tokens = tokens.len();
        
        // 🔧 动态调整batch和ubatch大小，确保能容纳prompt
        // n_batch和n_ubatch必须 >= prompt_tokens，否则会报"Insufficient Space"错误
        let min_batch_size = 512u32;  // 最小512
        let n_batch = prompt_tokens.max(min_batch_size as usize) as u32;
        let n_ubatch = prompt_tokens.max(256) as u32;  // ubatch也要足够大
        
        info!("LLM生成 - prompt_tokens: {}, n_batch: {}, n_ubatch: {}", prompt_tokens, n_batch, n_ubatch);
        
        // 创建上下文
        let ctx_params = LlamaContextParams::default()
            .with_n_ctx(std::num::NonZeroU32::new(n_ctx))
            .with_n_batch(n_batch)      // 动态batch：至少能容纳prompt
            .with_n_ubatch(n_ubatch)    // 动态ubatch：至少能容纳prompt
            .with_n_threads(n_threads as i32)
            .with_n_threads_batch(n_threads as i32);
        
        let mut ctx = self.model.new_context(backend, ctx_params)
            .context("上下文创建失败")?;
        
        // 创建batch（使用动态计算的batch大小）
        let mut batch = LlamaBatch::new(n_batch as usize, 1);
        
        // 添加prompt tokens到batch
        let last_index = (tokens.len() - 1) as i32;
        for (i, token) in tokens.iter().enumerate() {
            let is_last = i as i32 == last_index;
            batch.add(*token, i as i32, &[0], is_last)?;
        }
        
        // Decode
        ctx.decode(&mut batch).context("Decode失败")?;
        
        // 创建采样器
        let mut sampler = LlamaSampler::chain_simple([
            LlamaSampler::dist(1234),
            LlamaSampler::temp(temperature),
        ]);
        
        // 生成tokens
        let mut output = String::new();
        let mut n_cur = tokens.len();
        let n_len = n_cur + max_tokens as usize;
        
        while n_cur < n_len {
            // 采样
            let new_token_id = sampler.sample(&ctx, (batch.n_tokens() - 1) as i32);
            
            sampler.accept(new_token_id);
            
            // 检查是否为EOS
            if self.model.is_eog_token(new_token_id) {
                break;
            }
            
            // Token转文本
            if let Ok(piece) = self.model.token_to_str(new_token_id, llama_cpp_2::model::Special::Tokenize) {
                output.push_str(&piece);
            }
            
            // 准备下一次decode
            batch.clear();
            batch.add(new_token_id, n_cur as i32, &[0], true)?;
            
            ctx.decode(&mut batch).context("Decode失败")?;
            
            n_cur += 1;
        }
        
        let completion_tokens = n_cur - tokens.len();
        
        Ok((output, prompt_tokens, completion_tokens))
    }
}

// ==================== Embedding 模型包装 ====================

struct EmbeddingModelWrapper {
    model: LlamaModel,
    #[allow(dead_code)]
    model_path: String,  // 保留以便调试和日志记录
    dimension: usize,
    n_ctx: u32,
    n_threads: u32,
    n_batch: u32,
}

impl EmbeddingModelWrapper {
    fn new(backend: &LlamaBackend, path: PathBuf, config: &EmbeddingConfig) -> Result<Self> {
        info!("正在加载Embedding模型: {:?}", path);
        info!("配置: n_ctx={}, n_threads={}, n_batch={}", 
              config.n_ctx, config.n_threads, config.n_batch);
        
        let model_params = LlamaModelParams::default()
            .with_n_gpu_layers(0);  // Embedding模型用CPU
        
        let model = LlamaModel::load_from_file(backend, path.clone(), &model_params)
            .context("Embedding模型加载失败")?;
        
        info!("✅ Embedding模型加载成功");
        
        Ok(Self {
            model,
            model_path: path.to_string_lossy().to_string(),
            dimension: config.dimension,
            n_ctx: config.n_ctx,
            n_threads: config.n_threads,
            n_batch: config.n_batch,
        })
    }
    
    fn embed(&self, backend: &LlamaBackend, text: &str) -> Result<Vec<f32>> {
        // 详细日志：输出配置信息
        info!("🔍 Embedding请求 - 配置信息:");
        info!("   n_ctx: {}", self.n_ctx);
        info!("   n_batch: {}", self.n_batch);
        info!("   n_threads: {}", self.n_threads);
        info!("   文本长度: {} 字符", text.len());
        
        // 🔧 核心策略：为了保持速度，使用固定的batch size，并截断过长文本
        // BGE-M3模型支持最大8192 tokens，但为了平衡速度和容量，使用2048
        // 2048 tokens ≈ 约6000-8000字符，足够处理大部分embedding需求
        const MAX_EMBEDDING_TOKENS: usize = 2048;
        
        // Tokenize输入文本
        let mut tokens = self.model.str_to_token(text, AddBos::Always)
            .context("Tokenize失败")?;
        
        info!("   Tokenize结果: {} tokens", tokens.len());
        
        // 🔧 关键修复：如果tokens超过2048，直接截断
        // 这样可以保持固定的batch size，速度快且容量足够
        if tokens.len() > MAX_EMBEDDING_TOKENS {
            info!("⚠️ Embedding文本过长: {} tokens，截断到 {} tokens（保持速度）", 
                  tokens.len(), MAX_EMBEDDING_TOKENS);
            tokens.truncate(MAX_EMBEDDING_TOKENS);
        }
        
        // 使用固定的batch和ubatch参数，保持速度
        let batch_size = MAX_EMBEDDING_TOKENS;  // 2048，匹配最大token数
        let ubatch_size = MAX_EMBEDDING_TOKENS as u32;  // 2048
        
        info!("   使用固定配置: batch={}, ubatch={}, tokens={}", 
              batch_size, ubatch_size, tokens.len());
        
        // 创建上下文（使用固定参数，保持速度）
        let ctx_params = LlamaContextParams::default()
            .with_n_ctx(std::num::NonZeroU32::new(self.n_ctx))
            .with_n_batch(batch_size as u32)
            .with_n_ubatch(ubatch_size)
            .with_n_threads(self.n_threads as i32)
            .with_embeddings(true);
        
        let mut ctx = self.model.new_context(backend, ctx_params)
            .context("Embedding上下文创建失败")?;
        
        // 创建batch
        let mut batch = LlamaBatch::new(batch_size, 1);
        
        // 添加tokens到batch
        let last_index = (tokens.len() - 1) as i32;
        for (i, token) in tokens.iter().enumerate() {
            let is_last = i as i32 == last_index;
            batch.add(*token, i as i32, &[0], is_last)?;
        }
        
        info!("   Batch准备完成，开始decode...");
        
        // Decode生成embedding
        ctx.decode(&mut batch).context("Decode失败")?;
        
        // 获取embedding向量
        let embeddings = ctx.embeddings_seq_ith(0)
            .context("获取embedding失败")?;
        
        info!("✅ Embedding生成成功，维度: {}", embeddings.len());
        
        Ok(embeddings.to_vec())
    }
}

// ==================== 应用状态 ====================

struct AppState {
    model: Arc<RwLock<Option<ModelWrapper>>>,
    embedding_model: Arc<RwLock<Option<EmbeddingModelWrapper>>>,
    config: Config,
    _backend: LlamaBackend,
}

// ==================== API处理器 ====================

async fn health_check(State(state): State<Arc<AppState>>) -> Json<HealthResponse> {
    let model = state.model.read().await;
    Json(HealthResponse {
        status: "healthy".to_string(),
        model_loaded: model.is_some(),
        model_path: state.config.model.path.clone(),
        timestamp: Utc::now().to_rfc3339(),
    })
}

async fn list_models(State(state): State<Arc<AppState>>) -> Json<ModelsResponse> {
    Json(ModelsResponse {
        object: "list".to_string(),
        data: vec![ModelInfo {
            id: state.config.model.name.clone(),
            object: "model".to_string(),
            created: Utc::now().timestamp(),
            owned_by: "local".to_string(),
        }],
    })
}

async fn get_embedding(
    State(state): State<Arc<AppState>>,
    Json(req): Json<EmbeddingRequest>,
) -> Result<Response, AppError> {
    let embedding_guard = state.embedding_model.read().await;
    let embedding_model = embedding_guard.as_ref().ok_or(AppError::ModelNotLoaded)?;
    
    if req.text.is_empty() {
        return Err(AppError::InferenceError("文本不能为空".to_string()));
    }
    
    info!("收到Embedding请求 - 文本长度: {}", req.text.len());
    
    // 生成embedding
    let embedding_vec = embedding_model.embed(&state._backend, &req.text)
        .map_err(|e| AppError::InferenceError(e.to_string()))?;
    
    info!("Embedding生成成功 - 维度: {}", embedding_vec.len());
    
    let response = EmbeddingResponse {
        embedding: embedding_vec,
        dimension: embedding_model.dimension,
        model: state.config.embedding.as_ref()
            .map(|e| e.model_name.clone())
            .unwrap_or_else(|| "bge-m3".to_string()),
    };
    
    Ok(Json(response).into_response())
}

async fn chat_completions(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ChatCompletionRequest>,
) -> Result<Response, AppError> {
    use std::time::Instant;
    let start_time = Instant::now();
    
    let model_guard = state.model.read().await;
    let model = model_guard.as_ref().ok_or(AppError::ModelNotLoaded)?;
    
    let requested_model = if req.model.is_empty() {
        state.config.model.name.clone()
    } else {
        req.model.clone()
    };
    
    // OpenAI 标准默认值
    let temperature = req.temperature.unwrap_or(1.0);
    let max_tokens = req.max_tokens.unwrap_or(512);
    let _top_p = req.top_p.unwrap_or(1.0);  // 保留以便将来使用
    
    // 构建prompt (ChatML格式)
    let mut prompt = String::new();
    for msg in &req.messages {
        match msg.role.as_str() {
            "system" => prompt.push_str(&format!("<|im_start|>system\n{}<|im_end|>\n", msg.content)),
            "user" => prompt.push_str(&format!("<|im_start|>user\n{}<|im_end|>\n", msg.content)),
            "assistant" => prompt.push_str(&format!("<|im_start|>assistant\n{}<|im_end|>\n", msg.content)),
            _ => {}
        }
    }
    prompt.push_str("<|im_start|>assistant\n");
    
    // 动态计算需要的上下文大小：
    // 1. 先估算 prompt tokens（粗略估计：字符数/2，对中文可能更密集，乘以1.2安全系数）
    // 2. n_ctx = prompt_tokens + max_tokens + 安全边际（1024）
    // 3. 限制不超过配置的最大值
    let estimated_prompt_tokens = ((prompt.len() as f32 / 2.0) * 1.2) as u32;
    let required_ctx = (estimated_prompt_tokens + max_tokens as u32 + 1024).min(state.config.inference.n_ctx);
    
    info!(
        "收到请求 - 模型: {}, temp: {}, max_tokens: {}, 动态n_ctx: {}/{}, 消息数: {}", 
        requested_model, temperature, max_tokens, required_ctx, state.config.inference.n_ctx, req.messages.len()
    );
    
    // 生成（使用动态计算的上下文）
    let (response_text, prompt_tokens, completion_tokens) = model.generate(
        &state._backend,
        &prompt,
        max_tokens,
        temperature,
        state.config.inference.n_threads,
        required_ctx  // 使用动态计算的上下文大小
    ).map_err(|e| AppError::InferenceError(e.to_string()))?;
    
    let elapsed = start_time.elapsed();
    info!(
        "请求完成 - 耗时: {:.3}秒, Prompt tokens: {}, Completion tokens: {}, 速度: {:.1} t/s", 
        elapsed.as_secs_f64(), prompt_tokens, completion_tokens,
        completion_tokens as f64 / elapsed.as_secs_f64()
    );
    
    let response = ChatCompletionResponse {
        id: format!("chatcmpl-{}", Uuid::new_v4().simple()),
        object: "chat.completion".to_string(),
        created: Utc::now().timestamp(),
        model: requested_model,
        choices: vec![Choice {
            index: 0,
            message: Message {
                role: "assistant".to_string(),
                content: response_text,
            },
            finish_reason: "stop".to_string(),
        }],
        usage: Usage {
            prompt_tokens,
            completion_tokens,
            total_tokens: prompt_tokens + completion_tokens,
        },
    };
    
    Ok(Json(response).into_response())
}

// ==================== 错误处理 ====================

#[derive(Debug)]
enum AppError {
    ModelNotLoaded,
    InferenceError(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::ModelNotLoaded => (StatusCode::SERVICE_UNAVAILABLE, "Model not loaded".to_string()),
            AppError::InferenceError(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg),
        };
        (status, message).into_response()
    }
}

// ==================== 主函数 ====================

#[tokio::main]
async fn main() -> Result<()> {
    // 加载配置
    let config = Config::load().unwrap_or_else(|e| {
        eprintln!("⚠️ 加载配置失败: {}, 使用默认配置", e);
        Config::default()
    });
    
    // 初始化日志
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    info!("====================================");
    info!("  ERNIE 0.3B Llama.cpp 服务 (Rust)");
    info!("  OpenAI兼容API - 实际推理版本");
    info!("====================================");
    
    // 初始化llama backend
    let backend = LlamaBackend::init()?;
    info!("✅ Llama backend 初始化成功");
    
    // 加载LLM模型
    info!("正在加载LLM模型...");
    let model_path = PathBuf::from(&config.model.path);
    
    let model = match ModelWrapper::new(&backend, model_path, &config.inference) {
        Ok(m) => {
            info!("✅ LLM模型加载成功");
            Some(m)
        }
        Err(e) => {
            error!("❌ LLM模型加载失败: {}", e);
            error!("服务将启动但无法进行推理");
            None
        }
    };
    
    // 加载Embedding模型
    let embedding_model = if let Some(ref emb_config) = config.embedding {
        info!("正在加载Embedding模型...");
        let emb_path = PathBuf::from(&emb_config.model_path);
        
        match EmbeddingModelWrapper::new(&backend, emb_path, emb_config) {
            Ok(m) => {
                info!("✅ Embedding模型加载成功");
                Some(m)
            }
            Err(e) => {
                error!("❌ Embedding模型加载失败: {}", e);
                error!("服务将启动但无法使用Embedding功能");
                None
            }
        }
    } else {
        info!("⚠️  未配置Embedding模型");
        None
    };
    
    // 创建应用状态
    let state = Arc::new(AppState {
        model: Arc::new(RwLock::new(model)),
        embedding_model: Arc::new(RwLock::new(embedding_model)),
        config: config.clone(),
        _backend: backend,
    });
    
    // 构建路由
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/v1/models", get(list_models))
        .route("/v1/chat/completions", post(chat_completions))
        .route("/v1/embeddings", post(get_embedding))  // 新增embedding接口
        .route("/embedding", post(get_embedding))      // 兼容旧接口
        .layer(CorsLayer::permissive())
        .with_state(state);
    
    // 启动服务器
    let addr = format!("{}:{}", config.server.host, config.server.port);
    info!("====================================");
    info!("✅ 服务启动成功!");
    info!("====================================");
    info!("监听地址: http://{}", addr);
    info!("健康检查: http://localhost:{}/health", config.server.port);
    info!("模型列表: http://localhost:{}/v1/models", config.server.port);
    info!("聊天端点: http://localhost:{}/v1/chat/completions", config.server.port);
    info!("Embedding: http://localhost:{}/v1/embeddings", config.server.port);
    info!("====================================");
    
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .context("无法绑定端口")?;
    
    axum::serve(listener, app)
        .await
        .context("服务器启动失败")?;
    
    Ok(())
}