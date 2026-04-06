# Environment Variables Setup

## Backend (.env in beta/ folder)

Create a `.env` file in the `beta/` directory with:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_STORAGE_BUCKET=your-firebase-bucket.appspot.com

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# API Security
FB_SCRAPER_API_TOKEN=your-secure-random-token

# Optional: Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/diplom_db

# Optional: Google Sheets
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account",...}
```

## Frontend (.env.local in root folder)

Create a `.env.local` file in the root directory with:

```env
# Development
VITE_ENV=development

# Backend API
VITE_API_URL=http://localhost:8000
VITE_API_TOKEN=your-secure-random-token

# Optional: Gemini API key (if using client-side)
VITE_GEMINI_API_KEY=your-gemini-api-key

# Firebase (if using Firebase)
VITE_FIREBASE_PROJECT_ID=your-firebase-project-id
VITE_FIREBASE_API_KEY=your-firebase-api-key
```

## Production Deployment (Render)

Set these environment variables in Render dashboard:

1. Go to https://render.com/dashboard
2. Select your web service (diplom-backend)
3. Go to "Environment" tab
4. Add the following:

| Variable | Value |
|----------|-------|
| GEMINI_API_KEY | Get from https://ai.google.dev/ |
| FB_SCRAPER_API_TOKEN | Generate a secure token (e.g., using `openssl rand -hex 32`) |
| FIREBASE_PROJECT_ID | From Firebase console |
| FIREBASE_API_KEY | From Firebase console |
| FIREBASE_STORAGE_BUCKET | From Firebase console |

## Production Deployment (Vercel)

Set these environment variables in Vercel dashboard:

1. Go to https://vercel.com/dashboard
2. Select your project (Diplom-Data)
3. Go to "Settings" → "Environment Variables"
4. Add the following:

| Variable | Value |
|----------|-------|
| VITE_API_URL | https://diplom-backend.onrender.com |
| VITE_API_TOKEN | Same as FB_SCRAPER_API_TOKEN |

## Getting API Keys

### Gemini API Key
1. Visit https://ai.google.dev/
2. Click "Get API Key"
3. Create a new API key
4. Copy the key

### Firebase Project ID
1. Go to https://console.firebase.google.com/
2. Select your project
3. Go to Project Settings
4. Copy the Project ID and API Key

### Generate Secure Token
```bash
# macOS/Linux
openssl rand -hex 32

# PowerShell (Windows)
[Convert]::ToHexString($(New-Object System.Byte[] 32 | ForEach-Object { Get-Random -Max 256 }))
```

## Verifying Setup

Test environment variables locally:

```bash
# Backend
cd beta
python -c "import os; print('GEMINI_API_KEY:', 'Set' if os.getenv('GEMINI_API_KEY') else 'Not set')"

# Frontend
npm run build
grep "VITE_API_URL" dist/index.html
```

## Security Notes

⚠️ **Never commit .env files to Git!**

Use `.env.local` (Git ignored) or reference these guidelines for your CI/CD pipeline.

### .gitignore should contain:
```
.env
.env.local
.env.*.local
```

### Safe practices:
1. Use different tokens for dev/staging/production
2. Regenerate tokens if they leak
3. Use Render's secret variables for sensitive data
4. Rotate Gemini API keys periodically
