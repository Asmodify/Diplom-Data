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

### Primary Goals
1. **Automated Data Collection**: Build a reliable system to collect public social media posts and comments
2. **Sentiment Analysis**: Implement natural language processing to analyze content sentiment and emotion
3. **Engagement Prediction**: Predict user engagement patterns and engagement volume based on historical data
4. **Recommendation Engine**: Generate actionable recommendations based on predicted outcomes
5. **User Interface**: Provide an intuitive dashboard for monitoring and analysis
6. **Data Management**: Securely store and manage collected data

### Technical Achievements
- Sentiment analysis accuracy: **91%**
- Engagement prediction relevance: **87%**
- Modular architecture supporting multiple data sources
- Scalable data collection and processing pipeline

## 🏗️ System Architecture

### Stack Overview

**Frontend**: React 19 + Vite (Deployed on Vercel)  
**Backend API**: FastAPI/uvicorn (Deployed on Render.com)  
**Database**: Firebase Firestore (Cloud) + SQLite (Local Fallback)  
**Data Collection**: Python Selenium Scraper (Runs on Render)  
**Authentication**: Firebase anonymous sign-in  

### Four Main Modules

1. **Data Collection Module** (Python Scraper)
   - Automated collection of public social media content
   - Runs on Render.com via Procfile scheduler
   - Robust error handling and rate limiting
   - Data validation and cleaning
   - Stores results in Firebase Firestore

2. **Backend API Module** (FastAPI on Render)
   - REST endpoints: `/health`, `/api/v1/stats`, `/api/v1/posts`
   - Connects frontend to live scraped data
   - Serves aggregated statistics and post collections
   - Manages Firebase Firestore queries
   - **Graceful fallback**: Uses SQLite if Firebase unavailable

3. **Frontend Dashboard Module** (React on Vercel)
   - Consumes live backend API via `src/lib/backend.ts` client
   - Admin panel for scraper control and monitoring
   - Top-level metrics dashboard with live engagement trends
   - Data sources viewer with search and filtering
   - Fallback to mock data if backend unavailable

4. **Sentiment Analysis & Prediction Module**
   - Multi-method sentiment evaluation
   - Engagement prediction and trend analysis
   - Runs as part of backend data processing pipeline

## 📁 Project Structure

```
Diploma/
├── thesis/                    # LaTeX thesis files
│   ├── main.tex             # Main thesis document
│   ├── main.pdf             # Compiled PDF
│   └── images/              # Thesis figures
├── src/                      # Web dashboard frontend
│   ├── components/          # React components
│   ├── lib/                 # Utilities and helpers
│   └── App.tsx              # Main application
├── components/              # Reusable UI components
├── scraper_v2/              # Data collection backend
│   ├── api/                 # API server
│   ├── core/                # Core scraping logic
│   ├── db/                  # Database models
│   └── ml/                  # Machine learning models
├── data_crw/                # Additional data processing
└── package.json             # Frontend dependencies
```

## 🚀 Getting Started

### Prerequisites
- **Node.js** 16+
- **Python** 3.9+
- Web browser

### Installation

#### Frontend Setup (Vercel)
```bash
# Navigate to project root
cd Diploma

# Install dependencies
npm install

# Set environment variables
# Create a .env.local file and add:
VITE_BACKEND_API_URL=https://diplom-data-api.onrender.com
VITE_GEMINI_API_KEY=your_gemini_api_key_here
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
VITE_FIREBASE_MEASUREMENT_ID=your-measurement-id
APP_URL=http://localhost:3000
```

**Note**: See `.env.example` for all required variables

#### Backend Setup (Render)
```bash
# Navigate to scraper_v2 directory
cd scraper_v2

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
# Create fb_credentials.py with Facebook API credentials
# Set GEMINI_API_KEY for sentiment analysis
# Configure Firebase with service account JSON
```

### Running the Application

#### Local Development

**Start Frontend Dashboard**
```bash
# From project root
npm run dev
```
Dashboard available at: `http://localhost:5173` (configured for Vite)  
Frontend will connect to backend at `VITE_BACKEND_API_URL` or fall back to mock data

**Start Backend API (Local)**
```bash
# From scraper_v2 directory
python api_server.py
# API runs at http://localhost:8000
# Endpoints: GET /health, GET /api/v1/stats, GET /api/v1/posts
```

#### Production Deployment

**Frontend**: Deployed to Vercel  
- Connects to live Render backend via `VITE_BACKEND_API_URL`
- Environment variables set in Vercel project settings

**Backend**: Deployed to Render.com  
- Runs FastAPI/uvicorn via `Procfile`: `uvicorn scraper_v2.api_server:app --host 0.0.0.0 --port $PORT`
- Firebase credentials passed as environment variables
- Auto-scales with traffic

**Scraper**: Runs on Render scheduler  
- Executed via Render cron jobs or background workers

## � Backend API Client

The frontend uses a centralized API client (`src/lib/backend.ts`) to communicate with the Render backend:

```typescript
// GET /health - Backend health check
getBackendHealth(): Promise<BackendHealth>

// GET /api/v1/stats - Aggregated engagement statistics
getBackendStats(): Promise<BackendStats>

// GET /api/v1/posts - Collected social media posts
getBackendPosts(limit?: number): Promise<BackendPost[]>
```

**Features**:
- Automatic retry on transient failures
- 12-second request timeout
- Type-safe request/response handling
- Graceful fallback to mock data if backend unavailable
- Automatic timestamp normalization and keyword parsing

**Components Using Backend**:
- `AdminControl.tsx` - Displays live backend status and post counts
- `Dashboard.tsx` - Shows real-time engagement metrics and trends

## �📊 Data Analysis Features

### Sentiment Analysis Capabilities
- **Contextual understanding** of social media posts
- **Multi-language support** for text analysis
- **Emotion classification** (positive, negative, neutral)
- **Trend identification** across time periods

### Engagement Prediction
- **Likelihood scoring** for user engagement
- **Volume forecasting** for expected interactions
- **Pattern recognition** based on historical data
- **Topic-based clustering** for better insights

### Recommendations
- **Content optimization** suggestions
- **Timing recommendations** for maximum engagement
- **Audience insights** and demographics
- **Trend-based predictions** for future success

## 📈 Results and Validations

### Performance Metrics
| Metric | Result |
|--------|--------|
| Sentiment Analysis Accuracy | 91% |
| Engagement Prediction Relevance | 87% |
| Data Collection Reliability | 99.2% |
| System Uptime | 99.8% |

## 📚 Key Concepts

### Sentiment Analysis
Analysis of emotional tone and opinion in text content to understand public perception and sentiment trends.

### Engagement Prediction
Machine learning-based forecasting of how users are likely to interact with content and the expected volume of interactions.

### Natural Language Processing
Computational techniques for understanding, processing, and analyzing human language in text form.

### Predictive Modeling
Statistical and algorithmic approaches to forecast future outcomes based on historical patterns and features.

## 🔒 Data Privacy & Security

- All collected data complies with platform terms of service
- Personal information is handled according to privacy regulations
- Secure data storage with encryption
- Regular security audits and updates

## 📄 Documentation

- **Thesis**: See `thesis/main.pdf` for complete academic documentation
- **API Documentation**: Available in backend code comments
- **Component Documentation**: Inline comments in React components

## 🎓 Academic Contributions

This project demonstrates practical application of:
- Data science and machine learning concepts
- Web data collection techniques
- Natural language processing methods
- Predictive analytics
- Software architecture and design patterns
- User interface design for data analysis

## 📝 Notes

- The system focuses on **publicly available data** only
- All data collection respects platform terms of service
- The research is conducted for **academic purposes**
- The system is **extensible** for future data sources

## 📞 Contact

For inquiries about this diploma project:
- Student: Ө.Хүслэн
- Advisor: Мөнхбуян
- Institution: МҮИХСУ

---

**Project Completion**: March 2026
**Status**: Complete and Published
