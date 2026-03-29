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

### Four Main Modules

1. **Data Collection Module**
   - Automated collection of public social media content
   - Robust error handling and rate limiting
   - Data validation and cleaning

2. **Data Processing Module**
   - Text preprocessing and normalization
   - Feature extraction
   - Data enrichment

3. **Sentiment Analysis Module**
   - Multi-method sentiment evaluation
   - Emotion classification
   - Trend analysis

4. **Prediction & Recommendation Module**
   - Engagement likelihood prediction
   - Engagement volume forecasting
   - Automated recommendation generation

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

#### Frontend Setup
```bash
# Navigate to project root
cd Diploma

# Install dependencies
npm install

# Set environment variables
# Create a .env.local file and add:
# VITE_GEMINI_API_KEY=your_api_key_here
```

#### Backend Setup
```bash
# Navigate to scraper_v2 directory
cd scraper_v2

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API credentials (if needed)
# Edit fb_credentials.py and config.py as needed
```

### Running the Application

#### Start Frontend Dashboard
```bash
npm run dev
```
Dashboard available at: `http://localhost:3000`

#### Start Backend Services
```bash
# From scraper_v2 directory
python run.py
```

## 📊 Data Analysis Features

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
