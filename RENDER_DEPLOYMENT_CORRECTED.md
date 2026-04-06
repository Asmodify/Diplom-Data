# ⚠️ CORRECTED - Render Deployment Values

## ISSUE FOUND
Original build command was incorrect. Requirements.txt is in `beta/` subdirectory.

## CORRECTED Render Configuration

### Language
```
Python
```

### Branch
```
main
```

### Region
```
US East (Ohio)
```

### Root Directory
```
.
```

### Build Command (CORRECTED ⭐)
```
pip install -r beta/requirements.txt
```

**This is the correct path!**

### Start Command
```
python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT
```

### Environment Variables
| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Get from https://ai.google.dev/ |
| `FB_SCRAPER_API_TOKEN` | Generate secure token |
| `FIREBASE_PROJECT_ID` | From Firebase console |
| `FIREBASE_API_KEY` | From Firebase console |
| `FIREBASE_STORAGE_BUCKET` | From Firebase console |

---

## How to Fix Current Deployment

1. Go to https://render.com/dashboard
2. Select your service: `diplom-backend`
3. Go to **Settings** tab
4. Find **Build & Deploy** section
5. Update **Build Command** to: `pip install -r beta/requirements.txt`
6. Click **Save**
7. Go to **Deployments** tab and click **Manual Deploy**

Your deployment should now succeed! ✅
