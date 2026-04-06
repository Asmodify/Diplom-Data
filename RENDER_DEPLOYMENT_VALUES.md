# Render Deployment Quick Reference

## Render Configuration Questions & Answers

When Render asks for these fields, use these exact values:

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
Choose closest to you:
- US: US East (Ohio)
- EU: Frankfurt
- Asia: Singapore
Select based on where most users are
```

### Root Directory
```
.

(Leave empty or use . - this is the project root)
```

### Build Command
```
pip install -r requirements.txt
```

Copy this exactly!

### Start Command
```
python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT
```

Copy this exactly! (Note: $PORT is automatically set by Render)

### Environment Variables
Click "Advanced" and add these:

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Get from https://ai.google.dev/ (your Gemini API key) |
| `FB_SCRAPER_API_TOKEN` | Generate secure token (use openssl command) |
| `FIREBASE_PROJECT_ID` | Get from Firebase console |
| `FIREBASE_API_KEY` | Get from Firebase console |
| `FIREBASE_STORAGE_BUCKET` | Get from Firebase console |

---

## Step-by-Step Render Deployment

1. Go to https://render.com/dashboard
2. Click **"New +"** button
3. Select **"Web Service"**
4. 
   - Select your GitHub repo: **Asmodify/Diplom-Data**
   - Select branch: **main**
   - Click **"Connect"**

5. Fill in the form with values above:

   | Field | Value |
   |-------|-------|
   | Name | `diplom-backend` |
   | Runtime | `Python 3.11` |
   | Root Directory | `.` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python -m uvicorn beta.api_server:app --host 0.0.0.0 --port $PORT` |
   | Region | Choose closest |

6. Click **"Advanced"** to add environment variables

7. Add all environment variables from table above

8. Click **"Create Web Service"**

9. Wait 5-10 minutes for first deploy

10. Get your backend URL when ready:
    ```
    https://diplom-backend.onrender.com
    ```

---

## Generate Secure Token (if needed)

If you don't have `FB_SCRAPER_API_TOKEN`:

**PowerShell (Windows):**
```powershell
[Convert]::ToHexString($(New-Object System.Byte[] 32 | ForEach-Object { Get-Random -Max 256 }))
```

**Bash (macOS/Linux):**
```bash
openssl rand -hex 32
```

Example output:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

---

## Verify Deployment Works

Once deployed, test these URLs:

**Health Check:**
```
https://diplom-backend.onrender.com/health
```

**API Documentation:**
```
https://diplom-backend.onrender.com/docs
```

**Test Gemini:**
```bash
curl -X POST https://diplom-backend.onrender.com/gemini/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","analysis_type":"summary"}'
```

---

## Common Mistakes to Avoid

❌ Wrong:
- `pip install -r beta/requirements.txt` (specify full path)
- `python api_server.py` (direct run)
- Not including `--host 0.0.0.0` (won't be accessible)
- Using `PORT` instead of `$PORT` (Render specific syntax)

✅ Correct:
- `pip install -r requirements.txt` (from root)
- `python -m uvicorn beta.api_server:app ...` (module run)
- Include `--host 0.0.0.0` (listen on all interfaces)
- Use `$PORT` (Render variable)

---

## If First Deploy Fails

1. Go to service → **"Logs"** tab
2. Look for error message
3. Common fixes:
   - Check `requirements.txt` exists in root ✓
   - Check `beta/api_server.py` exists ✓
   - Check all environment variables are set ✓
   - Wait 30 seconds and rebuild

---

## Cost Information

- **Render Free Tier**: 750 hours/month (can run 24/7)
- **Render Paid Tier**: $7+/month for always-on hosting
- **Includes**: Automatic SSL, GitHub auto-deploy

Perfect for development and testing! ✓
