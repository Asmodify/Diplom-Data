# Social Media Data Collection and Predictive Analysis System

Diploma thesis project (2026) focused on collecting public social media data, analyzing sentiment, and predicting engagement trends.

## Thesis Information
- **Title (Mongolian):** Нийгмийн сүлжээний өгөгдлийн автомат цуглуулга ба таамаглалт шинжилгээний систем
- **Title (English):** Social Media Data Collection and Predictive Analysis System
- **Author:** Ө.Хүслэн (B221930045)
- **Advisor:** Мөнхбуян
- **Institution:** МУ-ИХСУ — Мэдээлэл холбооны технологийн сургууль

## Project Scope
- Automated collection of public social media posts/comments
- AI-powered sentiment and emotion analysis (Google Gemini)
- Engagement prediction and recommendation support
- Monitoring dashboard for data and backend health
- Firebase-backed storage and authentication

## Architecture at a Glance
| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite (Vercel) |
| Backend API | FastAPI (Render) |
| Data collection | Python scraper/Selenium |
| AI | Google Gemini API |
| Storage | Firebase Firestore (+ SQLite fallback) |

## Repository Structure
```text
Diplom-Data/
├── src/               # Frontend dashboard (React + Vite)
├── beta/              # Backend API, scraper, and ML/data logic
├── thesis/            # Thesis files and presentation assets
├── package.json       # Frontend scripts and dependencies
├── requirements.txt   # Root Python dependencies
└── render.yaml        # Render deployment config
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Git

### 1) Install dependencies
```bash
# from repository root
npm install

# backend dependencies
cd beta
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure environment
```bash
cp .env.example .env.local
```
Fill `.env.local` with Firebase, Gemini, and backend API values.

### 3) Run locally
```bash
# terminal 1: backend
cd beta
python api_server.py
```

```bash
# terminal 2: frontend (repo root)
npm run dev
```

Default local URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Useful Commands (root)
```bash
npm run dev
npm run lint
npm run build
```

## Deployment
- **Frontend:** Vercel
- **Backend:** Render (configured via `render.yaml`)
- Configure environment variables in both platforms before deployment.

## Privacy Note
- The system is designed for **publicly available** social media data.
- Data handling should follow platform terms and privacy regulations.
