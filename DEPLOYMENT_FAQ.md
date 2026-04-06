# Gemini Deployment FAQ - Questions & Answers

## Getting Started Questions

### Q: What do I need to deploy this?
**A:** You need:
1. GitHub account (already have ✓)
2. Render account (free tier available)
3. Vercel account (free tier available)
4. Google Gemini API key (free tier available)
5. Firebase project (optional, for data storage)

### Q: How much will this cost?
**A:** 
- **Render**: Free tier includes 750 hours/month (24/7 running), plenty for testing
- **Vercel**: Free tier includes unlimited deployments, great for frontend
- **Google Gemini API**: Free tier with 60 requests/minute, perfect for development
- **Total Cost**: $0 for development, ~$7-15/month for production if you upgrade

### Q: How long does deployment take?
**A:**
- Backend (Render): 5-10 minutes first deploy, then automatic on git push
- Frontend (Vercel): 1-3 minutes automatic redeploy on git push
- Total first time: ~15 minutes

---

## API Key & Credentials Questions

### Q: Where do I get the Gemini API key?
**A:**
1. Go to https://ai.google.dev/
2. Sign in with Google account
3. Click "Get API Key"
4. Create new API key
5. Copy the key (starts with `AIza...`)
6. Add to Render environment variables

### Q: Is the Gemini API key safe to share?
**A:** ❌ **NO** - Never share it!
- Keep it in environment variables only
- Never commit to GitHub
- If leaked, go to https://console.cloud.google.com/ and regenerate

### Q: Do I need a Firebase project?
**A:** No, it's optional. You can:
- Use just Gemini AI for analysis (works fine)
- Add Firebase later for persistent storage
- Use PostgreSQL instead if you prefer

### Q: What token should I use for FB_SCRAPER_API_TOKEN?
**A:** Generate a secure random token:

**Windows PowerShell:**
```powershell
[Convert]::ToHexString($(New-Object System.Byte[] 32 | ForEach-Object { Get-Random -Max 256 }))
```

**macOS/Linux:**
```bash
openssl rand -hex 32
```

Example output: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

---

## Deployment Questions

### Q: How do I deploy the backend to Render?
**A:**
1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repo (Asmodify/Diplom-Data)
4. Fill in these fields:
   - **Name**: diplom-backend
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT`
5. Click "Advanced" and add environment variables
6. Click "Create Web Service"
7. Wait for deployment ✓

### Q: How do I deploy the frontend to Vercel?
**A:**
1. Frontend auto-deploys when you push to `main` branch
2. Go to https://vercel.com/dashboard
3. Select "Diplom-Data" project
4. Add environment variables:
   - `VITE_API_URL` = `https://diplom-backend.onrender.com`
   - `VITE_API_TOKEN` = [same as FB_SCRAPER_API_TOKEN]
5. Redeploy project
6. Done! ✓

### Q: What if the first deploy fails?
**A:** Check logs:
1. **Render**: Go to service → "Logs" tab
2. **Vercel**: Go to project → "Deployments" → click failed deploy

Common errors:
- `ModuleNotFoundError`: Check `requirements.txt` has all packages
- `NameError`: Check environment variables are set
- `Connection refused`: Backend not running yet, wait 30 seconds

### Q: Can I test locally before deploying?
**A:** Yes!

**Backend:**
```bash
cd beta
python -m uvicorn api_server:app --reload
# Open http://localhost:8000/docs
```

**Frontend:**
```bash
npm run dev
# Open http://localhost:5173
```

---

## Environment Variables Questions

### Q: Where do I set environment variables?
**A:**

| Where | How |
|-------|-----|
| **Render (Backend)** | Dashboard → Service → Settings → Environment Variables |
| **Vercel (Frontend)** | Dashboard → Project → Settings → Environment Variables |
| **Local Dev** | Create `.env` in `beta/` folder for backend |

### Q: What environment variables do I need?
**A:**

**For Backend (Render):**
```env
GEMINI_API_KEY=AIza...
FB_SCRAPER_API_TOKEN=a1b2c3d4e5f6...
FIREBASE_PROJECT_ID=my-project
```

**For Frontend (Vercel):**
```env
VITE_API_URL=https://diplom-backend.onrender.com
VITE_API_TOKEN=a1b2c3d4e5f6...
```

### Q: Can I use .env files locally?
**A:** Yes, create files but **never commit to Git**:
- `beta/.env` for backend
- `.env.local` for frontend

Check `.gitignore` includes them ✓

---

## Testing Questions

### Q: How do I test if everything works?
**A:**

**Test 1: Health Check**
```bash
curl https://diplom-backend.onrender.com/health

# Expected: 
{
  "status": "healthy",
  "gemini": true,
  "firebase": true
}
```

**Test 2: Gemini Analysis**
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Machine learning rocks!","analysis_type":"summary"}'

# Expected: AI-generated summary
```

**Test 3: Ask Gemini**
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is machine learning?"}'

# Expected: AI answer
```

**Test 4: Frontend Component**
- Open https://diplom-data.vercel.app
- Use GeminiAnalyzer component
- Should work without errors

### Q: What if API returns 503?
**A:** Service not initialized:
- Check all environment variables are set ✓
- Check Render logs for errors
- Restart service in Render dashboard
- Wait 30 seconds for cold start

### Q: What if I get CORS errors?
**A:** Backend has open CORS, should work. If not:
1. Check API URL in browser DevTools
2. Verify `VITE_API_URL` is correct
3. Check backend is running: `curl https://diplom-backend.onrender.com/health`

---

## Features & Usage Questions

### Q: What can the GeminiAnalyzer component do?
**A:** Five analysis types:
1. **Summary** - 2-sentence overview
2. **Insights** - Key takeaways
3. **Questions** - Discussion questions
4. **Improvement** - How to make better
5. **Critique** - Constructive feedback

### Q: What can the GeminiQA component do?
**A:**
- Ask any question
- Optional context support
- Conversation history
- Copy answers to clipboard

### Q: Can I batch process multiple texts?
**A:** Yes, protected endpoint:
```typescript
const result = await apiClient.batchAnalyzeWithGemini(
  ['text 1', 'text 2', 'text 3'],
  'summary'
);
```
Max 20 texts per batch.

### Q: How do I integrate Gemini into my own component?
**A:**
```typescript
import { apiClient } from '@/lib/api';

// In your component:
const result = await apiClient.analyzeWithGemini(
  'Your text here',
  'summary' // or 'insights', 'questions', etc.
);

console.log(result.result); // AI response
```

---

## Troubleshooting

### Q: Backend shows "Gemini not initialized"
**A:**
1. Check `GEMINI_API_KEY` is set in Render
2. Check API key is valid and not expired
3. Go to https://console.cloud.google.com/ and verify quota
4. Restart service

### Q: Frontend can't reach backend
**A:**
1. Check `VITE_API_URL` is correct
2. Check backend URL is accessible: `curl https://diplom-backend.onrender.com/health`
3. Check firewall/proxy isn't blocking
4. Open Network tab in DevTools to see actual error

### Q: Getting "401 Unauthorized"
**A:**
1. Check `VITE_API_TOKEN` matches `FB_SCRAPER_API_TOKEN`
2. Protected endpoints require Bearer token
3. Use public endpoints first to test (no token needed)

### Q: Render keeps sleeping/restarting
**A:** Free tier sleeps after 15 minutes inactivity:
- Upgrade to paid tier ($7/month) for 24/7 running
- Or use `curl` to wake it up before use
- First request takes ~30 seconds

### Q: Gemini responses are slow
**A:**
- First request: primes model (~2-3 seconds)
- Subsequent: faster (~0.5-1 second)
- Render free tier adds ~1 second overhead
- This is normal!

### Q: How do I see backend logs?
**A:** In Render dashboard:
1. Select your service (diplom-backend)
2. Click "Logs" tab
3. Real-time logs appear
4. Search for errors

### Q: How do I see frontend logs?
**A:** In Vercel dashboard:
1. Select project (Diplom-Data)
2. Click "Deployments" → latest deploy
3. Scroll to "Build Logs"
4. Or check browser DevTools Console

---

## Performance Questions

### Q: How fast is Gemini?
**A:**
- Cold start: 2-3 seconds
- Warm response: 500ms - 1 second
- Batch (20 texts): 3-5 seconds

### Q: Can I make it faster?
**A:**
- Upgrade Render to paid tier (removes cold start)
- Batch multiple requests
- Cache responses for repeated queries
- Use simpler analysis types (summary is faster than questions)

### Q: What's my API rate limit?
**A:**
- Gemini Free: 60 requests/minute
- Gemini Pro: Much higher (paid)
- Protected endpoints: Only you can call
- Public endpoints: Open to all

---

## Production Readiness

### Q: Is this production-ready?
**A:** Mostly yes! ✓
- TypeScript: Validated
- Build: Tested
- API: Functional
- Security: Auth tokens implemented

**To make production-ready:**
1. Get SSL certificate (Render/Vercel do this automatically ✓)
2. Set strong tokens
3. Add rate limiting
4. Add error monitoring
5. Upgrade to paid tiers for reliability

### Q: What if I want to use the backend outside Render?
**A:** Just need:
1. Python 3.11+
2. `pip install -r requirements.txt`
3. Environment variables set
4. Run: `python -m uvicorn beta.api_server:app --host 0.0.0.0 --port 8000`

Works anywhere: Docker, AWS, Azure, GCP, local machine, etc.

---

## Getting Help

### Q: Where do I find more info?
**A:**
- **GEMINI_INTEGRATION_GUIDE.md** - Full setup with code examples
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step deployment
- **ENV_SETUP_GUIDE.md** - Environment variables reference
- **Backend Docs**: https://diplom-backend.onrender.com/docs (Swagger UI)

### Q: What if something breaks?
**A:**
1. Check the relevant guide above
2. Check logs (Render/Vercel dashboards)
3. Try local testing first
4. Restart services
5. Regenerate API keys if needed

### Q: How do I report bugs?
**A:** Create GitHub issue with:
1. What you tried
2. Error message
3. Expected vs actual behavior
4. Screenshots/logs if possible

---

## Summary Commands

**Deploy Backend:**
```bash
# Manual (if needed)
git push origin main
# Then Render auto-deploys
```

**Deploy Frontend:**
```bash
# Auto-deploys on git push
git push origin main
```

**Test Everything:**
```bash
# Backend health
curl https://diplom-backend.onrender.com/health

# Frontend access
# Open https://diplom-data.vercel.app

# API docs
# Open https://diplom-backend.onrender.com/docs
```

**Local Development:**
```bash
# Backend
cd beta
python -m uvicorn api_server:app --reload

# Frontend (new terminal)
npm run dev
```

---

This FAQ covers all common questions. If you have more, add them here! 📚
