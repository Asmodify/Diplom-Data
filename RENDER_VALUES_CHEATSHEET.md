# Render Deployment - Copy & Paste Values

Use these exact values when Render asks:

## Form Fields

**Language:** Python

**Branch:** main

**Region:** US East (Ohio)
*(or Frankfurt for EU, Singapore for Asia)*

**Root Directory:** .

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT
```

## Environment Variables (Click "Advanced")

| Variable Name | Value |
|---|---|
| GEMINI_API_KEY | *Get from https://ai.google.dev/* |
| FB_SCRAPER_API_TOKEN | *Generate: openssl rand -hex 32* |
| FIREBASE_PROJECT_ID | *From Firebase console* |
| FIREBASE_API_KEY | *From Firebase console* |
| FIREBASE_STORAGE_BUCKET | *From Firebase console* |

---

That's it! Click "Create Web Service" and wait 5-10 minutes.
