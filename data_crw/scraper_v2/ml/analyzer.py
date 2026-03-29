"""
Data Analyzer v2.0
===================
Basic data analysis and sentiment using TextBlob/VADER.

Features:
- Sentiment analysis (TextBlob, VADER)
- Text statistics
- Keyword extraction
- Language detection
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    logger.warning("TextBlob not installed. Install with: pip install textblob")

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    import nltk
    HAS_NLTK = True
    
    # Download required NLTK data
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    try:
        nltk.data.find('punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
except ImportError:
    HAS_NLTK = False
    logger.warning("NLTK not installed. Install with: pip install nltk")


class DataAnalyzer:
    """
    Basic data analysis for scraped content.
    
    Features:
    - Sentiment analysis (TextBlob or VADER)
    - Text statistics
    - Keyword extraction
    """
    
    def __init__(self, config=None):
        """
        Initialize DataAnalyzer.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        if config is None:
            from config import get_config
            config = get_config()
            
        self.config = config
        self._vader = None
        self._stopwords = set()
        
        # Initialize VADER if available
        if HAS_NLTK:
            try:
                self._vader = SentimentIntensityAnalyzer()
                self._stopwords = set(stopwords.words('english'))
            except Exception as e:
                logger.warning(f"VADER initialization failed: {e}")
                
    def analyze_sentiment(self, text: str, method: str = 'textblob') -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            method: 'textblob' or 'vader'
            
        Returns:
            Dictionary with sentiment scores
        """
        if not text or not text.strip():
            return {
                'score': 0.0,
                'label': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'method': method,
            }
            
        if method == 'vader' and self._vader:
            return self._analyze_vader(text)
        elif HAS_TEXTBLOB:
            return self._analyze_textblob(text)
        else:
            logger.warning("No sentiment analysis library available")
            return {'score': 0.0, 'label': 'neutral', 'method': 'none'}
            
    def _analyze_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine label
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
            
        return {
            'score': polarity,
            'label': label,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'method': 'textblob',
        }
        
    def _analyze_vader(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER."""
        scores = self._vader.polarity_scores(text)
        compound = scores['compound']
        
        # Determine label
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
            
        return {
            'score': compound,
            'label': label,
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'compound': compound,
            'method': 'vader',
        }
        
    def analyze_batch(self, texts: List[str], method: str = 'textblob') -> List[Dict[str, Any]]:
        """
        Analyze sentiment of multiple texts.
        
        Args:
            texts: List of texts
            method: Sentiment method
            
        Returns:
            List of sentiment results
        """
        return [self.analyze_sentiment(text, method) for text in texts]
        
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Extract top keywords from text.
        
        Args:
            text: Text to analyze
            top_n: Number of top keywords
            
        Returns:
            List of (keyword, count) tuples
        """
        if not text:
            return []
            
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove stopwords
        if self._stopwords:
            words = [w for w in words if w not in self._stopwords]
            
        # Count and return top
        counter = Counter(words)
        return counter.most_common(top_n)
        
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """
        Get basic text statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not text:
            return {
                'char_count': 0,
                'word_count': 0,
                'sentence_count': 0,
                'avg_word_length': 0,
            }
            
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
        }
        
    def analyze_comments(self, comments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a batch of comments.
        
        Args:
            comments: List of comment dictionaries
            
        Returns:
            Aggregated analysis results
        """
        if not comments:
            return {
                'total_comments': 0,
                'avg_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'keywords': [],
            }
            
        sentiments = []
        all_text = []
        distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for comment in comments:
            text = comment.get('text', '')
            if not text:
                continue
                
            all_text.append(text)
            result = self.analyze_sentiment(text)
            sentiments.append(result['score'])
            distribution[result['label']] += 1
            
        return {
            'total_comments': len(comments),
            'analyzed_count': len(sentiments),
            'avg_sentiment': sum(sentiments) / len(sentiments) if sentiments else 0.0,
            'sentiment_distribution': distribution,
            'keywords': self.extract_keywords(' '.join(all_text)),
        }
        
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code or None
        """
        if not text or not HAS_TEXTBLOB:
            return None
            
        try:
            blob = TextBlob(text)
            return blob.detect_language()
        except Exception:
            return None
