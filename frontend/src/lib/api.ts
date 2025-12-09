import axios from 'axios';
import { 
  AuthResponse, 
  Chatbot, 
  CreateChatbotPayload, 
  Document, 
  ChatMessage, 
  ChatResponse, 
  IngestResponse,
  TenantSettings,
  UsageStats,
  DeepEvalMetric,
  SignupRequest,
  SignupResponse,
} from '@/types'; // 使用 @ alias

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Interceptor to inject Token
api.interceptors.request.use(
  (config) => {
    // SSR Check
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('docbrain_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth Services
export const authService = {
  login: async (credentials: { email: string; password: string }): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },
  register: async (data: SignupRequest): Promise<SignupResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  }
};

// Stats Services
export const statsService = {
    getOverview: async (): Promise<UsageStats> => {
        // 由於後端暫時還沒有 /stats 端點，我們先回傳 Mock Data 讓 Dashboard 能顯示
        // 未來後端實作後，改為: const response = await api.get('/stats/overview'); return response.data;
        
        // 模擬延遲
        await new Promise(resolve => setTimeout(resolve, 600));

        return {
            chatbot_traffic: 12450,
            openai_usage: 45.20,
            llama_cloud_ops: 892,
            history: [
                { date: 'Mon', value: 120 },
                { date: 'Tue', value: 132 },
                { date: 'Wed', value: 101 },
                { date: 'Thu', value: 134 },
                { date: 'Fri', value: 290 },
                { date: 'Sat', value: 230 },
                { date: 'Sun', value: 210 }
            ]
        };
    }
};

// Chatbot Services
export const chatbotService = {
  list: async (): Promise<Chatbot[]> => {
    const response = await api.get<Chatbot[]>('/chatbots');
    return response.data;
  },
  create: async (payload: CreateChatbotPayload): Promise<Chatbot> => {
    const response = await api.post<Chatbot>('/chatbots', payload);
    return response.data;
  },
  update: async (id: string, payload: Partial<CreateChatbotPayload>): Promise<Chatbot> => {
    const response = await api.patch<Chatbot>(`/chatbots/${id}`, payload);
    return response.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/chatbots/${id}`);
  }
};

// Document Services
export const documentService = {
  list: async (_chatbotId: string): Promise<Document[]> => {
    const response = await api.get<Document[]>(`/document/${_chatbotId}/documents`);
    return response.data;
  },
  ingest: async (file: File, _chatbotId: string): Promise<IngestResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chatbot_id', _chatbotId);
    const response = await api.post<IngestResponse>('/document/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/document/${documentId}`);
  }
};

// Conversation Services
export const conversationService = {
  chat: async (publicId: string, messages: ChatMessage[]): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/conversation/chat', {
      public_id: publicId,
      messages
    });
    return response.data;
  }
};

// Tenant Settings
export const settingsService = {
    get: async (): Promise<TenantSettings> => {
        const response = await api.get('/settings/tenant');
        return response.data;
    },
    update: async (settings: TenantSettings): Promise<TenantSettings> => {
        const response = await api.patch('/settings/tenant', settings);
        return response.data;
    }
};

// Evaluation Services
export const evaluationService = {
    list: async (_chatbotId: string): Promise<DeepEvalMetric[]> => {
      // Mock Data for now — replace with real API when available
      return [
        { id: '1', query: 'What is the leave policy?', answer: '20 days paid leave.', faithfulness: 0.95, answer_relevance: 0.98, context_recall: 0.90, created_at: new Date().toISOString() },
        { id: '2', query: 'How to restart server?', answer: 'Use systemctl restart.', faithfulness: 0.88, answer_relevance: 0.92, context_recall: 0.85, created_at: new Date().toISOString() },
      ];
    },
    run: async (_chatbotId: string): Promise<void> => {
      // Mock Run — replace with real API call when implemented
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
};

export default api;