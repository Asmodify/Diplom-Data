# ✅ Render Deployment Checklist

## BEFORE YOU START
- [ ] You have a GitHub account
- [ ] `Asmodify/Diplom-Data` repo is set up and accessible
- [ ] You have a Firebase project created
- [ ] Code is committed and pushed to GitHub

---

## STEP 1: Get Firebase Credentials (5 mins)

1. [ ] Go to https://console.firebase.google.com/
2. [ ] Select your project
3. [ ] Settings ⚙️ → Project Settings → Service Accounts
4. [ ] Click "Generate New Private Key"
5. [ ] Save JSON file as `firebase_credentials.json` in `data_crw/beta/`
6. [ ] **DO NOT COMMIT TO GIT** (already in .gitignore)

**Verify:** File exists at `c:\Diploma\data_crw\beta\firebase_credentials.json`

---

## STEP 2: Push Code to GitHub (5 mins)

```bash
cd c:\Diploma

# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "Ready for Render deployment"

# Push
git push origin main
```

**Verify:** Check https://github.com/Asmodify/Diplom-Data/commits

---

## STEP 3: Create Render Service (10 mins)

1. [ ] Go to https://render.com
2. [ ] Sign up or log in (GitHub recommended)
3. [ ] Grant GitHub access
4. [ ] Click **New +** → **Web Service**
5. [ ] Select repository: `Asmodify/Diplom-Data`
6. [ ] Select branch: `main` (or `data_crw-migrated`)
7. [ ] Click **Continue**

---

## STEP 4: Configure Service Settings (5 mins)

| Setting | Value |
|---------|-------|
| Name | `diplom-data-api` |
| Runtime | `Python 3` |
| Root Directory | `data_crw/beta` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api_server:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Region | Choose closest to you |
| Plan | Free tier (for testing) |

8. [ ] Click **Create Web Service**
9. [ ] Watch the **Logs** tab

**Expected build time:** 5-10 minutes
**Success indicator:** Logs show "Deploying API" without errors

---

## STEP 5: Add Environment Variables (3 mins)

1. [ ] Go to your service dashboard
2. [ ] Click **Environment** tab
3. [ ] Click **Add Environment Variable**
   - Key: `FB_SCRAPER_API_TOKEN`
   - Value: Generate strong token (e.g., `sk_live_a1b2c3d4e5f6g7h8i9j0`)
4. [ ] Click **Save**

**Verify:** Shows in environment list

---

## STEP 6: Add Secret Files (3 mins)

1. [ ] Back in **Environment** tab
2. [ ] Scroll to **Secret Files**
3. [ ] Click **Add Secret File**
   - Filename: `firebase_credentials.json`
   - Contents: Paste entire JSON from file
   - Mount path: `/etc/secrets/firebase_credentials.json`
4. [ ] Click **Save**

5. [ ] Add second environment variable:
   - Key: `FIREBASE_CREDENTIALS`
   - Value: `/etc/secrets/firebase_credentials.json`
6. [ ] Click **Save**

**Verify:** Shows both in environment list

---

## STEP 7: Test Deployment (5 mins)

### Copy your service URL
Dashboard → Settings → Copy URL (e.g., `https://diplom-data-api.onrender.com`)

### Test endpoints:

**Health Check:**
```bash
curl https://diplom-data-api.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "firebase": true,
  "analyzer": true
}
```

**Swagger UI (Interactive docs):**
```
https://diplom-data-api.onrender.com/docs
```

**Get Posts (with auth):**
```bash
curl -H "Authorization: Bearer sk_live_a1b2c3d4e5f6g7h8i9j0" \
  https://diplom-data-api.onrender.com/api/v1/posts
```

- [ ] Health endpoint returns 200
- [ ] Swagger UI loads successfully
- [ ] Can access protected endpoints with token

---

## STEP 8: Connect Frontend (varies)

Update your React/Next.js code:

```javascript
const API_URL = "https://diplom-data-api.onrender.com";
const TOKEN = "sk_live_a1b2c3d4e5f6g7h8i9j0";

// Example fetch
fetch(`${API_URL}/api/v1/posts`, {
  headers: {
    "Authorization": `Bearer ${TOKEN}`,
    "Content-Type": "application/json"
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

- [ ] Frontend can successfully call API
- [ ] Data displays correctly

---

## STEP 9: Monitor & Maintain

- [ ] Bookmark your Render dashboard
- [ ] Enable email notifications (optional)
- [ ] Check **Metrics** weekly for performance
- [ ] Review **Logs** if issues occur

---

## TROUBLESHOOTING QUICK REFERENCE

| Issue | Solution |
|-------|----------|
| Build fails | Check logs, verify requirements.txt, redeploy |
| 503 Firebase error | Check secret file path and credentials content |
| 401 Unauthorized | Verify `FB_SCRAPER_API_TOKEN` matches in header |
| Timeout during build | Reduce dependencies, upgrade plan, or remove BERT |
| Service not responding | Check logs, health endpoint, and restart |

---

## USEFUL LINKS

- **Render Dashboard:** https://dashboard.render.com
- **Firebase Console:** https://console.firebase.google.com
- **GitHub Repo:** https://github.com/Asmodify/Diplom-Data
- **API Docs:** https://diplom-data-api.onrender.com/docs (after deploy)
- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

## TOTAL TIME ESTIMATE: 45-60 minutes

(Most time is waiting for Render to build and deploy)

---

## DONE! 🎉

Your API is now live and accessible globally!

**Next:** Connect your frontend and start using the live API.
