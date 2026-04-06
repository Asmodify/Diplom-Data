/**
 * API Client for Backend Communication
 * Handles all requests to the FastAPI backend with Gemini integration
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || 'dev-token-change-in-production';

interface ApiResponse<T = any> {
  status: string;
  data?: T;
  result?: string;
  answer?: string;
  error?: string;
  message?: string;
}

export class ApiClient {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string = API_URL, token: string = API_TOKEN) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add Bearer token for protected endpoints
    if (endpoint.includes('/api/v1/')) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        error.detail || `API Error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  // ==================== Health & Status ====================

  async healthCheck(): Promise<ApiResponse> {
    return this.request('/health');
  }

  // ==================== Gemini Endpoints ====================

  async analyzeWithGemini(
    text: string,
    analysisType:
      | 'summary'
      | 'insights'
      | 'questions'
      | 'improvement'
      | 'critique' = 'summary'
  ): Promise<ApiResponse> {
    return this.request('/gemini/analyze', {
      method: 'POST',
      body: JSON.stringify({
        text,
        analysis_type: analysisType,
      }),
    });
  }

  async askGemini(question: string, context?: string): Promise<ApiResponse> {
    return this.request('/gemini/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        context,
      }),
    });
  }

  async detectTopics(text: string): Promise<ApiResponse> {
    return this.request('/gemini/topics', {
      method: 'POST',
      body: JSON.stringify({
        text,
        analysis_type: 'summary',
      }),
    });
  }

  async batchAnalyzeWithGemini(
    texts: string[],
    analysisType: string = 'summary'
  ): Promise<ApiResponse> {
    if (texts.length > 20) {
      throw new Error('Maximum 20 texts per batch');
    }

    return this.request('/api/v1/gemini/batch-analyze', {
      method: 'POST',
      body: JSON.stringify({
        texts,
        analysis_type: analysisType,
      }),
    });
  }

  // ==================== Sentiment Analysis ====================

  async analyzeSentiment(text: string, language: string = 'en'): Promise<ApiResponse> {
    return this.request('/api/v1/sentiment', {
      method: 'POST',
      body: JSON.stringify({
        text,
        language,
      }),
    });
  }

  async batchAnalyzeSentiment(
    texts: string[],
    language: string = 'en'
  ): Promise<ApiResponse> {
    if (texts.length > 100) {
      throw new Error('Maximum 100 texts per batch');
    }

    return this.request('/api/v1/sentiment/batch', {
      method: 'POST',
      body: JSON.stringify({
        texts,
        language,
      }),
    });
  }

  // ==================== Trends & Topics ====================

  async getTrends(platform: string = 'facebook', limit: number = 10): Promise<ApiResponse> {
    const params = new URLSearchParams({
      platform,
      limit: Math.min(limit, 50).toString(),
    });

    return this.request(`/api/v1/trends?${params}`);
  }

  async getTopics(
    platform: string = 'facebook',
    limit: number = 10
  ): Promise<ApiResponse> {
    const params = new URLSearchParams({
      platform,
      limit: Math.min(limit, 50).toString(),
    });

    return this.request(`/api/v1/topics?${params}`);
  }

  // ==================== Statistics ====================

  async getStats(): Promise<ApiResponse> {
    return this.request('/stats');
  }

  // ==================== Utility ====================

  setToken(token: string): void {
    this.token = token;
  }

  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
