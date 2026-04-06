# Deployment Checklist: Gemini + Render + Vercel

## Pre-Deployment Verification ✅

- [x] Frontend TypeScript linter passes
- [x] Frontend production build successful
- [x] Backend API server configured with Gemini
- [x] Render deployment config created (`render.yaml`)
- [x] Environment variables documentation created
- [x] Example React components created

## Backend Deployment (Render)

### Step 1: Prepare Backend
```bash
cd beta
# Verify requirements.txt has google-generativeai
pip install -r requirements.txt
```

### Step 2: Deploy to Render
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect GitHub repo: `Asmodify/Diplom-Data`
4. Select branch: `main`
5. Configure:
   - **Name**: `diplom-backend`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT`
6. Click "Advanced"
7. Add Environment Variables:
   - `GEMINI_API_KEY`: [from ai.google.dev]
   - `FB_SCRAPER_API_TOKEN`: [generate secure token]
   - `FIREBASE_PROJECT_ID`: [from Firebase console]
8. Click "Create Web Service"
9. Wait 5-10 minutes for deployment
10. Get backend URL: `https://diplom-backend.onrender.com`

### Step 3: Test Backend
```bash
# Health check
curl https://diplom-backend.onrender.com/health

# Test Gemini endpoint
curl -X POST https://diplom-backend.onrender.com/gemini/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","analysis_type":"summary"}'
```

## Frontend Deployment (Vercel)

### Step 1: Update Frontend Config
Create `.env.production` (local, not in git):
```env
VITE_API_URL=https://diplom-backend.onrender.com
VITE_API_TOKEN=<same-as-FB_SCRAPER_API_TOKEN>
```

### Step 2: Commit Changes
```bash
git add -A
git commit -m "Add Gemini integration with API client and components"
git push origin main
```

### Step 3: Configure Vercel Environment
1. Go to https://vercel.com/dashboard
2. Select project: `Diplom-Data`
3. Go to "Settings" → "Environment Variables"
4. Add:
   - `VITE_API_URL`: `https://diplom-backend.onrender.com`
   - `VITE_API_TOKEN`: [same as FB_SCRAPER_API_TOKEN]
5. Redeploy from "Deployments" tab
6. Wait for deployment

### Step 4: Verify Frontend
1. Open https://diplom-data.vercel.app
2. Check browser console for errors
3. Look for `VITE_API_URL` in Network tab

## Integration Testing

### Test 1: Health Check Sequence
```bash
# 1. Backend health
curl https://diplom-backend.onrender.com/health

# 2. Expected response
{
  "status": "healthy",
  "version": "2.0.0",
  "firebase": true,
  "analyzer": true,
  "advanced_analyzer": true,
  "sheets": true,
  "gemini": true
}
```

### Test 2: Gemini Analysis
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning is transforming industries worldwide",
    "analysis_type": "insights"
  }'

# Expected: AI-generated insights
```

### Test 3: Q&A with Context
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to optimize data pipelines?",
    "context": "We use PostgreSQL and Firebase"
  }'

# Expected: Contextual answer
```

### Test 4: Frontend Component Usage
In React component:
```typescript
import { apiClient } from '@/lib/api';

// Test API client
const result = await apiClient.analyzeWithGemini(
  'Test content',
  'summary'
);
console.log(result);
```

## Monitoring & Troubleshooting

### Issue: 503 Gemini not initialized

**Solution**: Check Render environment variables
```bash
# In Render dashboard → diplom-backend → Environment
# Verify GEMINI_API_KEY is set and not empty
```

### Issue: CORS errors in browser

**Solution**: Backend is configured with open CORS, should work

### Issue: Slow first request

**Solution**: Render free tier sleeps after 15 min inactivity (30s startup)

### Issue: Build fails on Vercel

**Solution**: Check that `src/lib/api.ts` exists and tsconfig paths are correct

## Post-Deployment Checklist

- [ ] Backend deployed to Render
- [ ] Backend health endpoint returns 200
- [ ] GEMINI_API_KEY working (gemini field = true)
- [ ] Firebase connected (firebase field = true)
- [ ] Frontend deployed to Vercel
- [ ] Frontend loads without errors
- [ ] API client can make requests
- [ ] GeminiAnalyzer component renders
- [ ] GeminiQA component renders
- [ ] Gemini analysis endpoint returns AI output

## Next Steps

### Optional Enhancements
1. **WebSockets** for real-time analysis streaming
2. **Caching** with Redis for frequently asked questions
3. **Rate Limiting** on Gemini API calls
4. **Batch Processing** for large datasets
5. **Analytics** - track API usage

### Performance Optimization
1. Upgrade Render to paid tier (continuous running, 100GB bandwidth)
2. Add CDN caching headers
3. Implement request debouncing in frontend
4. Use response compression

### Monitoring Setup
1. Enable Render logs monitoring
2. Set up error alerts in Vercel
3. Track Gemini API usage
4. Monitor Firebase quota

## Files Created/Modified

### Backend
- ✅ `beta/ml/gemini_analyzer.py` - NEW Gemini integration module
- ✅ `beta/requirements.txt` - Added google-generativeai
- ✅ `beta/api_server.py` - Added Gemini endpoints
- ✅ `render.yaml` - NEW Render deployment config

### Frontend
- ✅ `src/lib/api.ts` - NEW API client
- ✅ `src/components/GeminiAnalyzer.tsx` - NEW analysis component
- ✅ `src/components/GeminiQA.tsx` - NEW Q&A component
- ✅ `tsconfig.json` - Fixed path aliases
- ✅ `.env.local` - Example environment file

### Documentation
- ✅ `GEMINI_INTEGRATION_GUIDE.md` - Comprehensive guide
- ✅ `ENV_SETUP_GUIDE.md` - Environment variables setup
- ✅ `DEPLOYMENT_CHECKLIST.md` - This file

## Quick Links

- Gemini API: https://ai.google.dev/
- Render Dashboard: https://render.com/dashboard
- Vercel Dashboard: https://vercel.com/dashboard
- Firebase Console: https://console.firebase.google.com/
- Backend Docs: https://diplom-backend.onrender.com/docs
