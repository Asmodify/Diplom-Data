# Deployment Guide (Vercel + Firebase)

This project can be deployed to both Vercel and Firebase Hosting.

## 1) Environment Variables

Set these in Vercel and in your local `.env` for development.

- `VITE_GEMINI_API_KEY`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

## 2) Vercel Deployment

1. Push repository to GitHub.
2. Import the project in Vercel.
3. Framework preset: Vite.
4. Build command: `npm run build`.
5. Output directory: `dist`.
6. Add environment variables listed above.
7. Deploy.

`vercel.json` is already added for SPA rewrite support.

## 3) Firebase Hosting Deployment

1. Install Firebase CLI:
   - `npm install -g firebase-tools`
2. Login:
   - `firebase login`
3. Set project ID in `.firebaserc` (replace `your-firebase-project-id`).
4. Build app:
   - `npm run build`
5. Deploy:
   - `firebase deploy --only hosting`

`firebase.json` is already configured for SPA rewrite support.

## 4) Optional: Dual Strategy

- Use Vercel for frontend hosting and preview deployments.
- Keep Firebase for database/auth/storage services.
- Or use Firebase Hosting for production and Vercel for staging.
