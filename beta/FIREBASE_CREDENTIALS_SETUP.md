# 🔐 Getting Your Firebase Credentials JSON

## Quick Steps:

### 1. Go to Firebase Console
- URL: https://console.firebase.google.com/
- Sign in with your Google account
- Select your project (e.g., `your-firebase-project`)

### 2. Navigate to Service Accounts
- Click the **Settings gear icon** (⚙️) at top-left
- Select **Project Settings**
- Go to **Service Accounts** tab
- You'll see a list of service accounts (usually one auto-created)

### 3. Generate Private Key
- Click on the service account email
- OR click **Generate New Private Key** button at bottom-right
- A JSON file will download automatically
- This is your credentials file!

### 4. Save the File
- Rename downloaded file to: `firebase_credentials.json`
- Save in: `c:\Diploma\data_crw\beta\`
- **IMPORTANT:** Never commit to Git!

### 5. Verify Content Structure
Your JSON should contain:
```json
{
  "type": "service_account",
  "project_id": "your-project-name",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----...",
  "client_email": "firebase-adminsdk-xxxxx@xxxxx.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

---

## For Render Deployment:

### 1. Copy Full JSON Content
- Open `firebase_credentials.json`
- Select ALL text (Ctrl+A)
- Copy it (Ctrl+C)

### 2. Add to Render
- Go to your Render service dashboard
- **Environment** tab
- Scroll to **Secret Files**
- **Add Secret File**
  - Filename: `firebase_credentials.json`
  - Contents: Paste your JSON
  - Mount path: `/etc/secrets/firebase_credentials.json`
- **Save**

### 3. Set Environment Variable
- Back in **Environment** tab
- **Add Environment Variable**
  - Key: `FIREBASE_CREDENTIALS`
  - Value: `/etc/secrets/firebase_credentials.json`
- **Save**

---

## Testing Locally

```bash
# Test Firebase connection
python -c "from db.firebase_db import FirebaseDB; db = FirebaseDB(); print('✓ Firebase connected!')"

# If successful, you'll see:
# ✓ Firebase Firestore initialized successfully
# ✓ Firebase connected!
```

---

## Troubleshooting

**Error: "FileNotFoundError: Firebase credentials not found"**
- Solution: Make sure `firebase_credentials.json` is in the correct directory

**Error: "Invalid credentials"**
- Solution: Regenerate the key in Firebase Console and re-download

**Error: "Permission denied"**
- Solution: Make sure your service account has Firestore permissions
- In Firebase: Rules should allow read/write for your service account

---

## Security Notes

✅ DO:
- Keep `firebase_credentials.json` file local only
- Add to `.gitignore` (already done in this repo)
- Store safely if sharing credentials

❌ DON'T:
- Commit credentials file to Git
- Share credentials in messages or emails
- Use in frontend code (backend only!)
- Rotate credentials unless compromised
