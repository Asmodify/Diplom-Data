# 🎟️ Render Deployment Quick Reference Card

## Copy-Paste Commands

### Test Locally
```bash
# Validate everything
python validate_deployment.py

# Start API
python run_local_server.py

# Visit: http://localhost:8000/docs
```

### Push to GitHub
```bash
cd c:\Diploma
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Get Firebase Token (in Python terminal)
```python
import secrets
print("sk_live_" + secrets.token_urlsafe(32))
```

---

## Render Dashboard Steps

### Step 1: Create Service
- URL: https://render.com → click **New +** → **Web Service**
- Select repo: `Asmodify/Diplom-Data`
- Choose branch: `main`

### Step 2: Configure
| Field | Value |
|-------|-------|
| Name | `diplom-data-api` |
| Runtime | `Python 3` |
| Root Dir | `data_crw/beta` |
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn api_server:app --host 0.0.0.0 --port $PORT` |
| Health | `/health` |

### Step 3: Env Variables
Go to **Environment** tab:
- Key: `FB_SCRAPER_API_TOKEN`
- Value: `sk_live_...` (generate with secrets module)

### Step 4: Secret Files
Scroll to **Secret Files**:
- Filename: `firebase_credentials.json`
- Contents: Paste full JSON from Firebase Console
- Mount path: `/etc/secrets/firebase_credentials.json`

### Step 5: Another Env Variable
- Key: `FIREBASE_CREDENTIALS`
- Value: `/etc/secrets/firebase_credentials.json`

### Step 6: Deploy
- Click **Create Web Service**
- Wait 5-10 minutes
- Check logs for errors

---

## Test Your API

### Get Your URL
Dashboard → Copy service URL (e.g., `https://diplom-data-api.onrender.com`)

### Test Health (no auth needed)
```bash
curl https://diplom-data-api.onrender.com/health
```

### Test with Auth
```bash
TOKEN="sk_live_your_token"
curl -H "Authorization: Bearer $TOKEN" \
  https://diplom-data-api.onrender.com/api/v1/posts
```

### View Interactive Docs
```
https://diplom-data-api.onrender.com/docs
```

---

## Get Firebase Credentials

### Quick Path:
1. https://console.firebase.google.com/
2. Select project
3. ⚙️ Settings → Service Accounts
4. Click **Generate New Private Key**
5. JSON downloads
6. Save as `firebase_credentials.json` in `data_crw/beta/`

---

## Environment Variables Needed

```
# For Render (REQUIRED)
FB_SCRAPER_API_TOKEN = sk_live_abc123...
FIREBASE_CREDENTIALS = /etc/secrets/firebase_credentials.json

# Optional
DEBUG = false
ENVIRONMENT = production
LOG_LEVEL = INFO
API_HOST = 0.0.0.0
API_PORT = 8000
```

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| Build fails | Run `pip install -r requirements.txt` locally first |
| Firebase error (503) | Check secret file path and content in Render |
| 401 Unauthorized | Missing `Authorization: Bearer TOKEN` header |
| Service won't start | Check logs for Python errors |
| Timeout during build | Remove BERT from requirements if using free tier |

---

## Files You Have

| File | Purpose |
|------|---------|
| RENDER_CHECKLIST.md | Step-by-step checklist ⭐ |
| RENDER_DEPLOYMENT_GUIDE.md | Detailed guide |
| API_USAGE_GUIDE.md | How to use API after deploy |
| FIREBASE_CREDENTIALS_SETUP.md | How to get credentials |
| render.yaml | Deployment config (YAML) |
| Procfile | Alternative deployment config |
| validate_deployment.py | Pre-deploy validation |
| run_local_server.py | Run API locally |
| .env.example | Local env template |
| .env.production | Production env reference |

---

## URLs You'll Need

| What | URL |
|-----|-----|
| Firebase Console | https://console.firebase.google.com |
| Render Dashboard | https://dashboard.render.com |
| GitHub Repo | https://github.com/Asmodify/Diplom-Data |
| API Health | https://YOUR_SERVICE.onrender.com/health |
| API Docs | https://YOUR_SERVICE.onrender.com/docs |

---

## API Endpoints Summary

```bash
TOKEN="sk_live_your_token"

# Health
curl https://YOUR_SERVICE.onrender.com/health

# Get posts
curl -H "Authorization: Bearer $TOKEN" \
  https://YOUR_SERVICE.onrender.com/api/v1/posts

# Get trends
curl -H "Authorization: Bearer $TOKEN" \
  https://YOUR_SERVICE.onrender.com/api/v1/trends

# Analyze sentiment
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Great!","language":"en"}' \
  https://YOUR_SERVICE.onrender.com/api/v1/sentiment

# Get stats
curl -H "Authorization: Bearer $TOKEN" \
  https://YOUR_SERVICE.onrender.com/api/v1/stats
```

---

## Time Breakdown

- Get Firebase credentials: **5 min**
- Push to GitHub: **5 min**
- Render setup: **10 min**
- Add env vars: **3 min**
- Wait for deploy: **10 min**
- Test: **5 min**
- **Total: ~40 minutes**

---

## Do's ✅ and Don'ts ❌

### ✅ DO:
- ✅ Change `FB_SCRAPER_API_TOKEN` to strong random string
- ✅ Keep Firebase credentials secure (never in Git)
- ✅ Test `/health` endpoint first
- ✅ Check Render logs if something fails
- ✅ Use HTTPS for all API calls

### ❌ DON'T:
- ❌ Commit `firebase_credentials.json` to Git
- ❌ Use weak tokens like "password" or "test123"
- ❌ Leave `DEBUG = true` in production
- ❌ Share your API token publicly
- ❌ Use BERT sentiment on free tier (too slow)

---

## Support

**In order of preference:**

1. Check RENDER_CHECKLIST.md
2. Check RENDER_DEPLOYMENT_GUIDE.md
3. Check Render logs in dashboard
4. Check FastAPI docs: https://fastapi.tiangolo.com
5. Check Firebase docs: https://firebase.google.com/docs

---

**Save this file! You can print it or bookmark it for quick reference.** 📌
