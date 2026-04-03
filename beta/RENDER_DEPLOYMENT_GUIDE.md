# 🚀 Complete Render.com Deployment Guide

## Overview
Deploy your FastAPI backend (`api_server.py`) to Render.com. Render will:
- Host your API on a live URL
- Manage SSL/HTTPS automatically
- Scale as needed
- Connect to Firebase Firestore

---

## Part 1: Preparation (Local Setup)

### 1.1 Verify Your Code is Ready

Your backend is ready to deploy:
- ✅ `api_server.py` - FastAPI app with endpoints
- ✅ `requirements.txt` - All dependencies listed
- ✅ `.env.example` - Environment template
- ✅ `/health` endpoint - For health checks
- ✅ `/docs` endpoint - Swagger UI
- ✅ `uvicorn` - Web server configured

### 1.2 Check Local Requirements

```bash
# From: c:\Diploma\data_crw\beta\

# Verify requirements.txt exists
ls requirements.txt

# Verify api_server.py is valid
python -m py_compile api_server.py
```

### 1.3 Get Firebase Service Account

**Steps:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** (gear icon) → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file as `firebase_credentials.json`
6. **Keep this file secure** - never commit to Git

---

## Part 2: GitHub Setup

### 2.1 Push Code to GitHub

Your repo: `https://github.com/Asmodify/Diplom-Data`

```bash
# From: c:\Diploma\

# Check git status
git status

# Add all changes
git add .

# Commit
git commit -m "Prepare API for Render deployment"

# Push to main (or your deployment branch)
git push origin main
```

### 2.2 Verify Remote Setup

```bash
git remote -v

# Should show:
# origin  https://github.com/Asmodify/Diplom-Data.git (fetch)
# origin  https://github.com/Asmodify/Diplom-Data.git (push)
```

---

## Part 3: Create Render Service

### 3.1 Sign Up / Log In

1. Go to https://render.com
2. Sign up with GitHub or email
3. Grant GitHub repo access when prompted

### 3.2 Create Web Service

**Steps:**

1. **Dashboard** → Click **New +** → Select **Web Service**

2. **Connect Repository:**
   - Select `Asmodify/Diplom-Data`
   - Choose branch: `main` (or `data_crw-migrated`)
   - Click **Continue**

3. **Configure Service:**
   - **Name:** `diplom-data-api`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn api_server:app --host 0.0.0.0 --port $PORT
     ```
   - **Root Directory:** `data_crw/beta`
   - **Health Check Path:** `/health`
   - **Health Check Protocol:** `HTTP`
   - **Region:** Choose closest to your users (US East recommended)
   - **Plan:** Free tier OK for testing

4. **Click Create Web Service**

### 3.3 Wait for Initial Deploy

Render will:
- Build your environment
- Install dependencies
- Start the server

Watch the **Logs** tab. You should see:
```
✓ Found python version 3.11
✓ Building Docker image
✓ npm packages found - skipping
✓ Building requirements from requirements.txt
...
✓ Deploying API
```

**Takes 5-10 minutes first time.**

---

## Part 4: Environment Variables (Critical!)

### 4.1 Add API Token

1. Go to your Render service dashboard
2. Click **Environment** tab
3. Click **Add Environment Variable**
4. **Key:** `FB_SCRAPER_API_TOKEN`
5. **Value:** Generate a strong token (use a password manager):
   ```
   Example: sk_live_abc123xyz789def456
   ```
6. Click **Save**

### 4.2 Add Firebase Path

1. **Key:** `FIREBASE_CREDENTIALS`
2. **Value:** `/etc/secrets/firebase_credentials.json`
3. Click **Save**

**Your env vars should now show:**
```
FB_SCRAPER_API_TOKEN = sk_live_abc123xyz789def456
FIREBASE_CREDENTIALS = /etc/secrets/firebase_credentials.json
PORT = 8000 (auto-set by Render)
```

---

## Part 5: Add Firebase Credentials (Secret File)

### 5.1 Upload Secret File

1. In Render service dashboard, go to **Environment** tab
2. Scroll down to **Secret Files**
3. Click **Add Secret File**
4. **Filename:** `firebase_credentials.json`
5. **Contents:** Paste your entire Firebase service account JSON

**Example structure:**
```json
{
  "type": "service_account",
  "project_id": "your-firebase-project",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

6. **Mount Path:** `/etc/secrets/firebase_credentials.json`
7. Click **Save**

Render will mount this at `/etc/secrets/firebase_credentials.json` automatically.

---

## Part 6: Test Your Deployment

### 6.1 Get Your Service URL

In Render dashboard:
- Copy your service URL (e.g., `https://diplom-data-api.onrender.com`)

### 6.2 Test Health Endpoint

```bash
curl https://diplom-data-api.onrender.com/health

# Response:
{
  "status": "healthy",
  "version": "2.0.0",
  "firebase": true,
  "analyzer": true,
  "advanced_analyzer": false,
  "sheets": false
}
```

### 6.3 Access Swagger UI

Open in browser:
```
https://diplom-data-api.onrender.com/docs
```

You should see interactive API docs.

### 6.4 Test Protected Endpoint

```bash
# Get posts (requires auth token)
curl -H "Authorization: Bearer sk_live_abc123xyz789def456" \
  https://diplom-data-api.onrender.com/api/v1/posts

# Response:
{
  "status": "success",
  "data": [...]
}
```

---

## Part 7: Common Configurations

### 7.1 If Using Advanced Sentiment Analysis (BERT)

Update `requirements.txt` to include:
```
torch>=2.0.0
transformers>=4.30.0
```

**Note:** This increases build time and memory. Render free tier may timeout.

### 7.2 If Using Google Sheets Export

1. Create a Google service account:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project
   - Enable Google Sheets API
   - Create Service Account
   - Download JSON key
   - Share a Google Sheet with the service account email

2. Add to Render as **Secret File:**
   - **Filename:** `google_sheets_credentials.json`
   - **Mount Path:** `/etc/secrets/google_sheets_credentials.json`

3. Add **Environment Variable:**
   - **Key:** `GOOGLE_SHEETS_CREDENTIALS`
   - **Value:** `/etc/secrets/google_sheets_credentials.json`

### 7.3 Custom Domain

1. Go to **Settings** tab
2. **Custom Domain** → Add your domain
3. Update DNS records in your domain provider
4. Render provides automatic HTTPS

---

## Part 8: Debugging & Logs

### 8.1 View Logs

In Render dashboard:
- Click **Logs** tab
- See real-time output
- Scroll to see build errors

### 8.2 Common Errors

**Error: "Module not found"**
```
Solution: Update requirements.txt and redeploy
```

**Error: "Firebase credentials not found"**
```
Solution: Verify secret file path is /etc/secrets/firebase_credentials.json
```

**Error: "503 Database not initialized"**
```
Solution: Firebase credentials invalid or network issue
- Check secret file in Render
- Test locally: python -c "from db.firebase_db import get_firebase_db; get_firebase_db()"
```

**Error: "401 Unauthorized"**
```
Solution: Wrong API token
- Check FB_SCRAPER_API_TOKEN environment variable
- Use: Authorization: Bearer <token>
```

### 8.3 Manual Redeploy

1. Push changes to GitHub
2. Render auto-deploys (watch **Deployments** tab)
3. Or click **Manual Deploy** button if needed

---

## Part 9: Monitor & Scale

### 9.1 View Metrics

**Dashboard** → **Metrics**
- CPU
- Memory
- Requests per minute
- Average response time

### 9.2 Scale CPU/Memory

**Settings** → **Instance Type**
- Free: 0.5 CPU, 512MB RAM
- Standard: 1 CPU, 2GB RAM ($7/month)
- Pro: 2 CPU, 4GB RAM ($19/month)

---

## Part 10: Final Checklist

- [ ] Code pushed to GitHub
- [ ] Service created on Render
- [ ] `FB_SCRAPER_API_TOKEN` env var set
- [ ] `FIREBASE_CREDENTIALS` env var set to `/etc/secrets/firebase_credentials.json`
- [ ] `firebase_credentials.json` secret file uploaded
- [ ] `/health` endpoint returns 200
- [ ] `/docs` accessible in browser
- [ ] API token works on protected endpoints
- [ ] Build time < 5 minutes
- [ ] No errors in logs after deploy

---

## Part 11: Connect Frontend to Deployed API

### In Your Frontend Code (React/TypeScript):

```typescript
// Update your API base URL
const API_BASE = "https://diplom-data-api.onrender.com";

// Example API call with auth
const fetchPosts = async (token: string) => {
  const response = await fetch(`${API_BASE}/api/v1/posts`, {
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    }
  });
  return response.json();
};
```

---

## Part 12: Backup & Recovery

### Keep These Safe:
1. `firebase_credentials.json` - Store in secure vault
2. `FB_SCRAPER_API_TOKEN` - Generate new one if leaked
3. GitHub repository link
4. Render project link

### To Migrate Later:
1. Export all data from Firestore
2. Update Render service settings
3. Re-upload credentials
4. Test new deployment

---

## 📞 Support

**Render Issues:**
- Docs: https://render.com/docs
- Status: https://status.render.com

**FastAPI Issues:**
- Docs: https://fastapi.tiangolo.com/
- Uvicorn: https://www.uvicorn.org/

**Firebase Issues:**
- Docs: https://firebase.google.com/docs
- Console: https://console.firebase.google.com/

---

## Next Steps

1. **Immediate:** Follow Part 3 to create service
2. **Short-term:** Test all endpoints
3. **Medium-term:** Connect frontend to deployed API
4. **Long-term:** Add custom domain, upgrade plan if needed

Good luck! 🎉
