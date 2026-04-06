# Gemini + Backend Integration Guide

## Architecture Overview

```
React Frontend (Vercel)
    ↓
FastAPI Backend (Render) with Gemini AI
    ↓
Firebase (Data storage)
    ↓
Google Gemini API (AI analysis)
```

## Step 1: Deploy Backend to Render

### 1.1 Create Render Account
- Go to https://render.com
- Sign up with GitHub account

### 1.2 Connect GitHub Repository
1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repo (Asmodify/Diplom-Data)
4. Select branch: `main`

### 1.3 Configure Service
- **Name**: `diplom-backend`
- **Region**: Choose closest to you (e.g., Frankfurt, US East)
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT`

### 1.4 Add Environment Variables
Click "Advanced" and add:

```
GEMINI_API_KEY=<your-gemini-api-key>
FB_SCRAPER_API_TOKEN=<secure-token>
FIREBASE_PROJECT_ID=<your-firebase-project>
```

**Get Gemini API Key:**
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create new API key
4. Copy and paste into Render

### 1.5 Deploy
- Click "Create Web Service"
- Wait 5-10 minutes for deployment
- Get your backend URL: `https://diplom-backend.onrender.com`

## Step 2: Verify Backend Endpoints

Open your browser and test:

```
https://diplom-backend.onrender.com/health
https://diplom-backend.onrender.com/docs  (Swagger docs)
```

## Step 3: Connect Frontend to Backend

### 3.1 Update `.env.local` in React Frontend

Create file at root: `.env.local`

```env
VITE_API_URL=https://diplom-backend.onrender.com
VITE_API_TOKEN=<your-fb-scraper-token>
VITE_GEMINI_API_KEY=<your-gemini-key>
```

### 3.2 Create API Client

Create `src/lib/api.ts`:

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TOKEN = import.meta.env.VITE_API_TOKEN || 'dev-token-change-in-production';

export const apiClient = {
  async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
        ...options.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  },

  // Gemini endpoints
  async analyzeWithGemini(text: string, analysisType: string = 'summary') {
    return this.request('/gemini/analyze', {
      method: 'POST',
      body: JSON.stringify({ text, analysis_type: analysisType }),
    });
  },

  async askGemini(question: string, context?: string) {
    return this.request('/gemini/ask', {
      method: 'POST',
      body: JSON.stringify({ question, context }),
    });
  },

  async detectTopics(text: string) {
    return this.request('/gemini/topics', {
      method: 'POST',
      body: JSON.stringify({ text, analysis_type: 'summary' }),
    });
  },

  // General endpoints
  async getStats() {
    return this.request('/stats');
  },

  async getTrends(limit: number = 10) {
    return this.request(`/trends?limit=${limit}`);
  },

  async analyzeSentiment(text: string) {
    return this.request('/api/v1/sentiment', {
      method: 'POST',
      body: JSON.stringify({ text, language: 'en' }),
    });
  },

  async healthCheck() {
    return this.request('/health');
  },
};
```

### 3.3 Use API in Components

**Example: Sentiment Analysis Component**

```typescript
import { useState } from 'react';
import { apiClient } from '@/lib/api';

export function SentimentAnalyzer() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    setLoading(true);
    try {
      const data = await apiClient.analyzeSentiment(text);
      setResult(data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to analyze..."
        className="w-full p-3 border rounded"
      />
      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
      {result && (
        <div className="bg-gray-100 p-4 rounded">
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
```

## Step 4: Use Gemini in Frontend

### 4.1 Content Summary Component

```typescript
export function ContentSummary({ text }: { text: string }) {
  const [summary, setSummary] = useState('');
  const [insights, setInsights] = useState('');

  async function generate() {
    const summaryData = await apiClient.analyzeWithGemini(text, 'summary');
    setSummary(summaryData.result);

    const insightData = await apiClient.analyzeWithGemini(text, 'insights');
    setInsights(insightData.result);
  }

  return (
    <div className="space-y-4">
      <button onClick={generate} className="bg-green-500 text-white px-4 py-2 rounded">
        Generate Summary & Insights
      </button>
      {summary && (
        <div>
          <h3 className="font-bold">Summary</h3>
          <p>{summary}</p>
        </div>
      )}
      {insights && (
        <div>
          <h3 className="font-bold">Key Insights</h3>
          <p>{insights}</p>
        </div>
      )}
    </div>
  );
}
```

### 4.2 Q&A Component

```typescript
export function GeminiQA() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  async function ask() {
    const result = await apiClient.askGemini(question);
    setAnswer(result.answer);
  }

  return (
    <div className="space-y-4">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask Gemini..."
        className="w-full p-3 border rounded"
      />
      <button onClick={ask} className="bg-purple-500 text-white px-4 py-2 rounded">
        Ask
      </button>
      {answer && <div className="bg-blue-100 p-4 rounded">{answer}</div>}
    </div>
  );
}
```

## Step 5: Available API Endpoints

### Gemini Endpoints (No Auth Required)
- `POST /gemini/analyze` - Analyze text
- `POST /gemini/ask` - Ask questions
- `POST /gemini/topics` - Detect topics

### Protected Endpoints (Require Bearer Token)
- `POST /api/v1/sentiment` - Sentiment analysis
- `POST /api/v1/sentiment/batch` - Batch analysis
- `GET /api/v1/trends` - Get trending topics
- `POST /api/v1/gemini/batch-analyze` - Batch Gemini analysis (max 20 texts)

### General Endpoints
- `GET /health` - Health check
- `GET /stats` - Get statistics
- `GET /docs` - Swagger documentation

## Step 6: Deploy Updated Frontend

### 6.1 Commit Changes
```bash
git add -A
git commit -m "Add Gemini integration and API client"
git push origin main
```

### 6.2 Vercel Auto-Deploy
Vercel automatically deploys when you push to main. Check deployment at:
- https://diplom-data.vercel.app

## Testing

### Test 1: Backend Health
```bash
curl https://diplom-backend.onrender.com/health
```

### Test 2: Gemini Analysis
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"This is amazing!","analysis_type":"sentiment"}'
```

### Test 3: Ask Gemini
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is machine learning?"}'
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 503 Gemini not initialized | Check GEMINI_API_KEY in Render env vars |
| CORS errors | Backend allows all origins by default |
| Slow first request | Render free tier sleeps, request wakes it (30 sec) |
| Auth token errors | Check FB_SCRAPER_API_TOKEN environment variable |

## Next Steps

1. ✅ Backend deployed on Render
2. ✅ Frontend deployed on Vercel
3. ✅ Gemini AI integrated
4. 🔄 Add real-time updates with WebSockets (optional)
5. 🔄 Set up monitoring/logging
6. 🔄 Upgrade to paid Render for better performance

## Environment Variables Checklist

| Variable | Where | Value |
|----------|-------|-------|
| GEMINI_API_KEY | Render | From ai.google.dev |
| FB_SCRAPER_API_TOKEN | Render | Generate secure token |
| FIREBASE_PROJECT_ID | Render | From Firebase console |
| VITE_API_URL | .env.local (Frontend) | https://diplom-backend.onrender.com |
| VITE_API_TOKEN | .env.local (Frontend) | Same as FB_SCRAPER_API_TOKEN |
