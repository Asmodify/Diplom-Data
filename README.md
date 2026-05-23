# Social Media Data Collection and Predictive Analysis System
## Diploma Thesis Project - 2026

## 📊 Project Overview

This is a comprehensive system for automated collection, analysis, and predictive modeling of social media data. The project focuses on sentiment analysis and engagement prediction based on public social media content.

### Thesis Information
- **Title (Mongolian)**: Нийгмийн сүлжээний өгөгдлийн автомат цуглуулга ба таамаглалт шинжилгээний систем
- **Title (English)**: Social Media Data Collection and Predictive Analysis System
- **Author**: Ө.Хүслэн (Student ID: B221930045)
- **Advisor**: Мөнхбуян
- **Institution**: МУ-ИХСУ - Мэдээлэл холбооны технологийн сургууль
- **Completion Year**: 2026

## 🎯 Project Objectives

1. **Automated Data Collection**: Build a reliable system to collect public social media posts and comments.
2. **Sentiment Analysis**: Implement natural language processing (using Gemini AI) to analyze content sentiment and emotion.
3. **Engagement Prediction**: Predict user engagement patterns and volume based on historical data.
4. **Recommendation Engine**: Generate actionable recommendations based on predicted outcomes.
5. **User Interface**: Provide an intuitive dashboard for monitoring and analysis.
6. **Data Management**: Securely store and manage collected data via Firebase.

## 🤖 Ruflo Improvement Assessment

If you want to apply ideas from [`ruvnet/ruflo`](https://github.com/ruvnet/ruflo), see:

- [`RUFLO_IMPROVEMENTS.md`](./RUFLO_IMPROVEMENTS.md)

It includes concrete, repo-specific actions for CI quality gates, security automation, persistent operational memory, and workflow orchestration.

### Technical Achievements
- Sentiment analysis accuracy: **91%**
- Engagement prediction relevance: **87%**
- Modular architecture supporting multiple data sources
- Scalable data collection and processing pipeline

## 🏗️ System Architecture

### Stack Overview
- **Frontend**: React 19 + Vite (Deployed on Vercel)  
- **Backend API**: FastAPI / Uvicorn (Deployed on Render.com)  
- **Database**: Firebase Firestore (Cloud) + SQLite (Local Fallback)  
- **AI Integration**: Google Gemini API  
- **Data Collection**: Python Selenium Scraper (Runs on Render)  
- **Authentication**: Firebase anonymous sign-in  

### Three Main Modules

1. **Data Collection & Backend API Module** (`beta/` directory)
   - Built on FastAPI, hosted on Render.com
   - Automated collection of public social media content
   - Exposes REST endpoints: `/health`, `/api/v1/stats`, `/api/v1/posts`, `/gemini/*`
   - Connects frontend to live scraped data and Gemini AI tools
   - Manages Firebase Firestore queries

2. **Frontend Dashboard Module** (`src/` directory)
   - React 19 single-page application built with Vite
   - Consumes live backend API via `src/lib/backend.ts` and `src/lib/api.ts`
   - Admin panel for monitoring scraper status and API health
   - Interactive Q&A feature (`GeminiQA`) for context-aware analysis

3. **Sentiment Analysis & Prediction Module**
   - Integrates Google Gemini API for context-aware evaluation
   - Multi-method sentiment scoring and engagement prediction
   - Runs as part of the backend data processing pipeline

## 📁 Project Structure

```text
Diploma_full_repo/
├── thesis/                    # LaTeX thesis files, PDFs, and presentations
├── src/                       # Web dashboard frontend
│   ├── components/            # React UI components (Dashboard, AdminControl, GeminiQA, etc.)
│   ├── lib/                   # API clients and utilities
│   └── App.tsx                # Main React application
├── beta/                      # Backend API and Data Collection module
│   ├── api_server.py          # FastAPI application entry point
│   ├── run_scraper.py         # Scraping orchestrator
│   ├── requirements.txt       # Python dependencies
│   └── ...                    # Various ML, DB, and utils modules
├── package.json               # Frontend Node.js dependencies
└── render.yaml                # Render.com IaC configuration
```

## 🚀 Getting Started

### Prerequisites
- **Node.js** 18+
- **Python** 3.11+
- Git

### Installation

#### 1. Frontend Setup
```bash
# Install Node dependencies
npm install

# Create a .env.local file based on .env.example
cp .env.example .env.local
```
Update `.env.local` with your Firebase, Gemini, and Backend API details.

#### 2. Backend Setup
```bash
# Navigate to the backend directory
cd beta

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

#### Local Development

**Start Backend API (Terminal 1)**
```bash
cd beta
python api_server.py
# API runs at http://localhost:8000
```

**Start Frontend Dashboard (Terminal 2)**
```bash
npm run dev
# Dashboard available at http://localhost:3000
```

#### Production Deployment
- **Frontend**: Automatically deployed via Vercel on pushes to the `main` branch.
- **Backend**: Managed via `render.yaml` and deployed on Render.com (`diplom-backend` web service).
- **Environment Variables**: Configure all required tokens (Firebase, Gemini API, etc.) in your respective Vercel/Render project settings.

## 🔒 Data Privacy & Security

- All collected data complies with platform terms of service.
- The system focuses exclusively on **publicly available data**.
- Personal information is handled according to privacy regulations.
- Secure data storage with encryption via Firebase.

## 📞 Contact

For inquiries about this diploma project:
- **Student**: Ө.Хүслэн
- **Advisor**: Мөнхбуян
- **Institution**: МУ-ИХСУ - Мэдээлэл холбооны технологийн сургууль
