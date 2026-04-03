"""
Machine Learning Analysis Module
Provides sentiment analysis, topic classification, and engagement prediction
using Scikit-Learn and CatBoost
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation, PCA
from sklearn.metrics import classification_report, mean_squared_error, r2_score
import joblib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import os

# Try importing CatBoost
try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("⚠ CatBoost not available, using sklearn alternatives")

# Try importing TextBlob for sentiment
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠ TextBlob not available, using basic sentiment analysis")

# Try importing NLTK
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    
    # Download required NLTK data
    for resource in ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)
    
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠ NLTK not available, using basic text processing")


class DataAnalyzer:
    """
    Comprehensive ML analyzer for Facebook scraper data
    Provides sentiment analysis, topic classification, and engagement prediction
    """
    
    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize the analyzer
        
        Args:
            models_dir: Directory to save/load trained models
        """
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            self.models_dir = Path(__file__).parent.parent / 'models'
        
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize vectorizers
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        self.count_vectorizer = CountVectorizer(
            max_features=1000,
            stop_words='english'
        )
        
        # Initialize scalers
        self.engagement_scaler = StandardScaler()
        
        # Trained models
        self.sentiment_model = None
        self.topic_model = None
        self.engagement_model = None
        
        # Topic labels (will be set during training)
        self.topic_labels = None
        
        print("✓ DataAnalyzer initialized")
    
    # ==================== TEXT PREPROCESSING ====================
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove mentions and hashtags (but keep the word)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        if NLTK_AVAILABLE:
            try:
                # Tokenize
                tokens = word_tokenize(text)
                
                # Remove stopwords and lemmatize
                stop_words = set(stopwords.words('english'))
                lemmatizer = WordNetLemmatizer()
                
                tokens = [
                    lemmatizer.lemmatize(token) 
                    for token in tokens 
                    if token not in stop_words and len(token) > 2
                ]
                
                text = ' '.join(tokens)
            except:
                pass
        
        return text
    
    def extract_features(self, posts: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract features from posts for ML models"""
        features = []
        
        for post in posts:
            content = post.get('content', '') or ''
            
            feature = {
                'post_id': post.get('post_id', ''),
                'content': content,
                'content_clean': self.preprocess_text(content),
                'content_length': len(content),
                'word_count': len(content.split()) if content else 0,
                'has_hashtags': '#' in content,
                'hashtag_count': content.count('#'),
                'has_mentions': '@' in content,
                'mention_count': content.count('@'),
                'has_urls': 'http' in content.lower(),
                'has_emoji': bool(re.search(r'[^\w\s,.]', content)),
                'exclamation_count': content.count('!'),
                'question_count': content.count('?'),
                'likes': post.get('likes', 0),
                'shares': post.get('shares', 0),
                'comment_count': post.get('comment_count', 0),
                'page_name': post.get('page_name', ''),
            }
            
            # Add time-based features if timestamp available
            timestamp = post.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = None
                
                if timestamp:
                    feature['hour'] = timestamp.hour
                    feature['day_of_week'] = timestamp.weekday()
                    feature['is_weekend'] = timestamp.weekday() >= 5
            
            features.append(feature)
        
        return pd.DataFrame(features)
    
    # ==================== SENTIMENT ANALYSIS ====================
    
    def analyze_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze sentiment of posts
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping post_id to sentiment results
        """
        results = {}
        
        for post in posts:
            post_id = post.get('post_id', '')
            content = post.get('content', '') or ''
            
            if not content:
                results[post_id] = {
                    'sentiment': 'neutral',
                    'polarity': 0.0,
                    'subjectivity': 0.0,
                    'confidence': 0.0
                }
                continue
            
            if TEXTBLOB_AVAILABLE:
                # Use TextBlob for sentiment analysis
                blob = TextBlob(content)
                polarity = blob.sentiment.polarity  # -1 to 1
                subjectivity = blob.sentiment.subjectivity  # 0 to 1
                
                # Classify sentiment
                if polarity > 0.1:
                    sentiment = 'positive'
                elif polarity < -0.1:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
                
                confidence = abs(polarity)
            else:
                # Basic sentiment using keyword matching
                positive_words = ['good', 'great', 'amazing', 'love', 'excellent', 'happy', 
                                'wonderful', 'fantastic', 'best', 'awesome', 'thank']
                negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'sad', 
                                'disappointed', 'angry', 'horrible', 'poor', 'wrong']
                
                content_lower = content.lower()
                pos_count = sum(1 for word in positive_words if word in content_lower)
                neg_count = sum(1 for word in negative_words if word in content_lower)
                
                if pos_count > neg_count:
                    sentiment = 'positive'
                    polarity = min(pos_count / 5, 1.0)
                elif neg_count > pos_count:
                    sentiment = 'negative'
                    polarity = -min(neg_count / 5, 1.0)
                else:
                    sentiment = 'neutral'
                    polarity = 0.0
                
                subjectivity = 0.5
                confidence = abs(polarity)
            
            results[post_id] = {
                'sentiment': sentiment,
                'polarity': round(polarity, 4),
                'subjectivity': round(subjectivity, 4) if TEXTBLOB_AVAILABLE else 0.5,
                'confidence': round(confidence, 4)
            }
        
        return results
    
    def train_sentiment_classifier(self, posts: List[Dict[str, Any]], 
                                    labels: List[str]) -> Dict[str, float]:
        """
        Train a custom sentiment classifier
        
        Args:
            posts: List of post dictionaries
            labels: Sentiment labels ('positive', 'neutral', 'negative')
            
        Returns:
            Training metrics
        """
        df = self.extract_features(posts)
        
        # Prepare text data
        texts = df['content_clean'].fillna('').tolist()
        
        # Encode labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(labels)
        
        # Vectorize text
        X = self.tfidf_vectorizer.fit_transform(texts)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        if CATBOOST_AVAILABLE:
            self.sentiment_model = CatBoostClassifier(
                iterations=100,
                learning_rate=0.1,
                depth=6,
                verbose=False
            )
            self.sentiment_model.fit(X_train.toarray(), y_train)
            y_pred = self.sentiment_model.predict(X_test.toarray())
        else:
            self.sentiment_model = LogisticRegression(max_iter=1000)
            self.sentiment_model.fit(X_train, y_train)
            y_pred = self.sentiment_model.predict(X_test)
        
        # Evaluate
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save model
        self._save_model('sentiment_model', self.sentiment_model)
        joblib.dump(self.tfidf_vectorizer, self.models_dir / 'tfidf_vectorizer.joblib')
        joblib.dump(label_encoder, self.models_dir / 'sentiment_label_encoder.joblib')
        
        return {
            'accuracy': report['accuracy'],
            'precision': report['weighted avg']['precision'],
            'recall': report['weighted avg']['recall'],
            'f1_score': report['weighted avg']['f1-score']
        }
    
    # ==================== TOPIC CLASSIFICATION ====================
    
    def classify_topics(self, posts: List[Dict[str, Any]], 
                        n_topics: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Classify posts into topics using LDA
        
        Args:
            posts: List of post dictionaries
            n_topics: Number of topics to identify
            
        Returns:
            Dictionary mapping post_id to topic results
        """
        df = self.extract_features(posts)
        texts = df['content_clean'].fillna('').tolist()
        
        # Skip if no valid text
        valid_texts = [t for t in texts if t.strip()]
        if len(valid_texts) < 5:
            return {post.get('post_id', ''): {
                'topic': 0,
                'topic_name': 'insufficient_data',
                'topic_probability': 0.0,
                'keywords': []
            } for post in posts}
        
        # Vectorize with count vectorizer for LDA
        try:
            X = self.count_vectorizer.fit_transform(texts)
        except ValueError:
            # All texts might be empty
            return {post.get('post_id', ''): {
                'topic': 0,
                'topic_name': 'unknown',
                'topic_probability': 0.0,
                'keywords': []
            } for post in posts}
        
        # Train LDA model
        n_topics = min(n_topics, len(valid_texts))
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20
        )
        
        topic_distributions = lda.fit_transform(X)
        
        # Get feature names
        feature_names = self.count_vectorizer.get_feature_names_out()
        
        # Generate topic labels based on top keywords
        self.topic_labels = []
        topic_keywords = []
        
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-5:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            topic_keywords.append(keywords)
            self.topic_labels.append(f"topic_{topic_idx}_{keywords[0]}")
        
        # Assign topics to posts
        results = {}
        for i, post in enumerate(posts):
            post_id = post.get('post_id', '')
            
            if i < len(topic_distributions):
                topic_dist = topic_distributions[i]
                dominant_topic = np.argmax(topic_dist)
                topic_prob = topic_dist[dominant_topic]
                
                results[post_id] = {
                    'topic': int(dominant_topic),
                    'topic_name': self.topic_labels[dominant_topic],
                    'topic_probability': round(float(topic_prob), 4),
                    'keywords': topic_keywords[dominant_topic],
                    'all_topics': {
                        self.topic_labels[j]: round(float(p), 4)
                        for j, p in enumerate(topic_dist)
                    }
                }
            else:
                results[post_id] = {
                    'topic': 0,
                    'topic_name': 'unknown',
                    'topic_probability': 0.0,
                    'keywords': []
                }
        
        # Save model
        self._save_model('topic_model', lda)
        
        return results
    
    # ==================== ENGAGEMENT PREDICTION ====================
    
    def predict_engagement(self, posts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Predict engagement metrics for posts
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping post_id to engagement predictions
        """
        df = self.extract_features(posts)
        
        # Calculate engagement score (combination of likes, shares, comments)
        df['engagement_score'] = (
            df['likes'] + 
            df['shares'] * 2 +  # Shares weighted more
            df['comment_count'] * 1.5
        )
        
        # Prepare features for prediction
        feature_cols = [
            'content_length', 'word_count', 'hashtag_count', 
            'mention_count', 'exclamation_count', 'question_count'
        ]
        
        # Add time features if available
        if 'hour' in df.columns:
            feature_cols.extend(['hour', 'day_of_week'])
        
        # Fill missing values
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = df[col].fillna(0)
        
        X = df[feature_cols].values
        
        # If we have enough data, train a model
        results = {}
        
        if len(posts) >= 10:
            y = df['engagement_score'].values
            
            # Scale features
            X_scaled = self.engagement_scaler.fit_transform(X)
            
            # Train model (use cross-validation for small datasets)
            if CATBOOST_AVAILABLE:
                model = CatBoostRegressor(
                    iterations=50,
                    learning_rate=0.1,
                    depth=4,
                    verbose=False
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=50,
                    max_depth=4,
                    random_state=42
                )
            
            model.fit(X_scaled, y)
            predictions = model.predict(X_scaled)
            
            # Calculate percentiles for classification
            high_threshold = np.percentile(y, 75)
            low_threshold = np.percentile(y, 25)
            
            for i, post in enumerate(posts):
                post_id = post.get('post_id', '')
                actual = float(df.iloc[i]['engagement_score'])
                predicted = float(predictions[i])
                
                # Classify engagement level
                if predicted >= high_threshold:
                    level = 'high'
                elif predicted <= low_threshold:
                    level = 'low'
                else:
                    level = 'medium'
                
                results[post_id] = {
                    'engagement_score': round(actual, 2),
                    'predicted_score': round(predicted, 2),
                    'engagement_level': level,
                    'likes': int(df.iloc[i]['likes']),
                    'shares': int(df.iloc[i]['shares']),
                    'comments': int(df.iloc[i]['comment_count']),
                    'features': {
                        'content_length': int(df.iloc[i]['content_length']),
                        'word_count': int(df.iloc[i]['word_count']),
                        'hashtag_count': int(df.iloc[i]['hashtag_count'])
                    }
                }
            
            # Save model
            self._save_model('engagement_model', model)
            joblib.dump(self.engagement_scaler, self.models_dir / 'engagement_scaler.joblib')
        else:
            # Not enough data for training, just return stats
            for i, post in enumerate(posts):
                post_id = post.get('post_id', '')
                score = float(df.iloc[i]['engagement_score'])
                
                results[post_id] = {
                    'engagement_score': round(score, 2),
                    'predicted_score': round(score, 2),
                    'engagement_level': 'unknown',
                    'likes': int(df.iloc[i]['likes']),
                    'shares': int(df.iloc[i]['shares']),
                    'comments': int(df.iloc[i]['comment_count']),
                    'features': {
                        'content_length': int(df.iloc[i]['content_length']),
                        'word_count': int(df.iloc[i]['word_count']),
                        'hashtag_count': int(df.iloc[i]['hashtag_count'])
                    }
                }
        
        return results
    
    # ==================== COMPREHENSIVE ANALYSIS ====================
    
    def analyze_all(self, posts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Run all analyses on posts
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping post_id to all analysis results
        """
        sentiment_results = self.analyze_sentiment(posts)
        topic_results = self.classify_topics(posts)
        engagement_results = self.predict_engagement(posts)
        
        combined = {}
        for post in posts:
            post_id = post.get('post_id', '')
            combined[post_id] = {
                'sentiment': sentiment_results.get(post_id, {}),
                'topic': topic_results.get(post_id, {}),
                'engagement': engagement_results.get(post_id, {}),
                'analyzed_at': datetime.utcnow().isoformat()
            }
        
        return combined
    
    def get_summary_stats(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics from analysis"""
        analysis = self.analyze_all(posts)
        
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        engagement_levels = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        topics = {}
        
        for post_id, results in analysis.items():
            # Count sentiments
            sentiment = results.get('sentiment', {}).get('sentiment', 'neutral')
            if sentiment in sentiments:
                sentiments[sentiment] += 1
            
            # Count engagement levels
            level = results.get('engagement', {}).get('engagement_level', 'unknown')
            if level in engagement_levels:
                engagement_levels[level] += 1
            
            # Count topics
            topic = results.get('topic', {}).get('topic_name', 'unknown')
            topics[topic] = topics.get(topic, 0) + 1
        
        return {
            'total_posts': len(posts),
            'sentiment_distribution': sentiments,
            'engagement_distribution': engagement_levels,
            'topic_distribution': topics,
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    # ==================== MODEL PERSISTENCE ====================
    
    def _save_model(self, name: str, model: Any):
        """Save a trained model"""
        path = self.models_dir / f'{name}.joblib'
        joblib.dump(model, path)
        print(f"✓ Model saved: {path}")
    
    def _load_model(self, name: str) -> Optional[Any]:
        """Load a trained model"""
        path = self.models_dir / f'{name}.joblib'
        if path.exists():
            return joblib.load(path)
        return None
    
    def load_trained_models(self):
        """Load all previously trained models"""
        self.sentiment_model = self._load_model('sentiment_model')
        self.topic_model = self._load_model('topic_model')
        self.engagement_model = self._load_model('engagement_model')
        
        # Load vectorizers and scalers
        tfidf_path = self.models_dir / 'tfidf_vectorizer.joblib'
        if tfidf_path.exists():
            self.tfidf_vectorizer = joblib.load(tfidf_path)
        
        scaler_path = self.models_dir / 'engagement_scaler.joblib'
        if scaler_path.exists():
            self.engagement_scaler = joblib.load(scaler_path)


# Convenience function
def get_analyzer(models_dir: Optional[str] = None) -> DataAnalyzer:
    """Get a DataAnalyzer instance"""
    return DataAnalyzer(models_dir)
