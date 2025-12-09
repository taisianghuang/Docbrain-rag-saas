export interface User {
  id: string;
  email: string;
  company_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

export enum RagMode {
  VECTOR = "vector",
  HYBRID = "hybrid",
  ROUTER = "router",
  SENTENCE_WINDOW = "sentence_window",
  PARENT_CHILD = "parent_child"
}

export enum ChunkingStrategy {
  STANDARD = "standard",
  MARKDOWN = "markdown",
  SEMANTIC = "semantic",
  WINDOW = "window"
}

export interface RagConfig {
  mode: RagMode;
  chunking_strategy: ChunkingStrategy;
  llm_model: string;
  top_k: number;
  temperature: number;
}

export interface WidgetConfig {
  title: string;
  primary_color: string;
  welcome_message: string;
}

export interface Chatbot {
  id: string;
  name: string;
  public_id: string;
  rag_config: RagConfig;
  widget_config: WidgetConfig;
  is_active: boolean;
  created_at?: string;
}

export interface CreateChatbotPayload {
  name: string;
  rag_config: RagConfig;
  widget_config: WidgetConfig;
}

export interface Document {
  id: string;
  name: string;
  status: 'processing' | 'indexed' | 'error';
  created_at: string;
  chatbot_id: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  id?: string;
}

export interface SourceNodeMetadata {
  filename?: string;
  // 使用 unknown 允許其他額外欄位，但不像 any 那樣寬鬆
  [key: string]: unknown;
}

export interface SourceNode {
  node_id: string;
  text: string;
  score: number;
  metadata?: SourceNodeMetadata;
}

export interface ChatResponse {
  response: string;
  source_nodes: SourceNode[];
}

export interface IngestResponse {
  status: string;
  document_id: string;
  chunks: number;
}

export interface TenantSettings {
  tenant_id?: string;
  openai_key_configured?: boolean;
  llama_cloud_key_configured?: boolean;
  openai_key?: string;
  llama_cloud_key?: string;
}

export interface UsageStats {
  chatbot_traffic: number;
  openai_usage: number; // in tokens or USD
  llama_cloud_ops: number;
  history: { date: string; value: number }[];
}

export interface DeepEvalMetric {
  id: string;
  query: string;
  answer: string;
  context_recall: number;
  faithfulness: number;
  answer_relevance: number;
  created_at: string;
}

// 註冊用的 Request Body 
export interface SignupRequest {
  email: string;
  password: string;
  company_name?: string;
  openai_key?: string | null;
  llama_cloud_key?: string | null;
}

// 前端表單資料（始終用字串，避免 Input 元件的 type 錯誤）
export interface SignupFormData {
  email: string;
  password: string;
  company_name: string;
  openai_key: string;
  llama_cloud_key: string;
}

export interface SignupResponse {
  account_id: string;
  tenant_id: string;
  email: string;
  company_name: string;
  message: string;
}