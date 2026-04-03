"""
Advanced Sentiment Analyzer with BERT Support
Provides enhanced sentiment analysis with emotion detection and sarcasm detection
Adapted from SOCIAL-MEDIA-ANALYTICS for integration with Facebook scraper
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path

# Try importing PyTorch and Transformers for BERT support
try:
    import torch
    import torch.nn as nn
    from transformers import BertTokenizer, BertModel
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("⚠ PyTorch/Transformers not available, BERT sentiment disabled")

# Fallback to TextBlob
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


class AdvancedSentimentAnalyzer:
    """
    Advanced sentiment analysis using BERT-based models
    Supports multi-language sentiment detection with emotion classification
    Falls back to TextBlob if BERT dependencies not available
    """
    
    SENTIMENT_LABELS = ['negative', 'neutral', 'positive']
    EMOTION_LABELS = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'trust', 'anticipation']
    
    def __init__(self, model_name: str = 'bert-base-uncased', models_dir: Optional[str] = None):
        """
        Initialize the sentiment analyzer
        
        Args:
            model_name: Name of the BERT model to use
            models_dir: Directory to save/load model weights
        """
        self.models_dir = Path(models_dir) if models_dir else Path(__file__).parent.parent / 'models'
        self.models_dir.mkdir(exist_ok=True)
        
        self.use_bert = BERT_AVAILABLE
        
        if self.use_bert:
            self._init_bert(model_name)
        else:
            print("ℹ Using TextBlob for sentiment analysis")
        
        # Sarcasm detection patterns
        self.sarcasm_indicators = [
            'yeah right', 'sure', 'totally', 'obviously', 'of course',
            'great job', 'well done', 'fantastic', 'brilliant', 'wonderful',
            'how nice', 'just great', 'thanks a lot', 'nice one'
        ]
    
    def _init_bert(self, model_name: str):
        """Initialize BERT models"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"ℹ Using device: {self.device}")
        
        try:
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.bert_model = BertModel.from_pretrained(model_name).to(self.device)
            self.bert_model.eval()
            
            # Sentiment classification head
            self.sentiment_classifier = nn.Sequential(
                nn.Linear(768, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 3)  # Positive, Negative, Neutral
            ).to(self.device)
            
            # Emotion classification head
            self.emotion_classifier = nn.Sequential(
                nn.Linear(768, 256),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(256, 8)  # 8 emotions
            ).to(self.device)
            
            # Try loading pre-trained weights
            self._load_weights()
            
            print("✓ BERT sentiment analyzer initialized")
        except Exception as e:
            print(f"⚠ Failed to initialize BERT: {e}")
            self.use_bert = False
    
    def analyze(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """
        Analyze sentiment and emotions in text
        
        Args:
            text: Input text to analyze
            language: Language code (en, es, fr, etc.)
        
        Returns:
            Dictionary with sentiment and emotion analysis
        """
        if not text or not text.strip():
            return self._empty_result(text, language)
        
        # Preprocess text
        clean_text = self._preprocess_text(text)
        
        if self.use_bert:
            return self._analyze_bert(text, clean_text, language)
        elif TEXTBLOB_AVAILABLE:
            return self._analyze_textblob(text, clean_text, language)
        else:
            return self._analyze_basic(text, clean_text, language)
    
    def analyze_batch(self, texts: List[str], language: str = 'en') -> List[Dict]:
        """
        Analyze multiple texts in batch for efficiency
        
        Args:
            texts: List of texts to analyze
            language: Language code
        
        Returns:
            List of analysis results
        """
        if not self.use_bert:
            return [self.analyze(text, language) for text in texts]
        
        results = []
        batch_size = 32
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            clean_batch = [self._preprocess_text(t) for t in batch]
            
            # Tokenize batch
            inputs = self.tokenizer(
                clean_batch,
                return_tensors='pt',
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :]
                
                # Predictions
                sentiment_logits = self.sentiment_classifier(embeddings)
                sentiment_probs = torch.softmax(sentiment_logits, dim=1)
                
                emotion_logits = self.emotion_classifier(embeddings)
                emotion_probs = torch.softmax(emotion_logits, dim=1)
            
            # Process each result
            for j, (orig_text, clean_text) in enumerate(zip(batch, clean_batch)):
                sentiment_idx = torch.argmax(sentiment_probs[j]).item()
                
                results.append({
                    'text': orig_text[:200] + '...' if len(orig_text) > 200 else orig_text,
                    'language': language,
                    'sentiment': {
                        'label': self.SENTIMENT_LABELS[sentiment_idx],
                        'score': sentiment_probs[j][sentiment_idx].item(),
                        'distribution': {
                            label: prob.item()
                            for label, prob in zip(self.SENTIMENT_LABELS, sentiment_probs[j])
                        }
                    },
                    'emotions': self._get_top_emotions(emotion_probs[j]),
                    'sarcasm': {
                        'detected': self._detect_sarcasm(clean_text, sentiment_probs[j]) > 0.7,
                        'score': self._detect_sarcasm(clean_text, sentiment_probs[j])
                    }
                })
        
        return results
    
    def _analyze_bert(self, original_text: str, clean_text: str, language: str) -> Dict:
        """Analyze using BERT"""
        # Tokenize
        inputs = self.tokenizer(
            clean_text,
            return_tensors='pt',
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Get BERT embeddings
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
            
            # Sentiment prediction
            sentiment_logits = self.sentiment_classifier(embeddings)
            sentiment_probs = torch.softmax(sentiment_logits, dim=1)
            sentiment_idx = torch.argmax(sentiment_probs, dim=1).item()
            
            # Emotion prediction
            emotion_logits = self.emotion_classifier(embeddings)
            emotion_probs = torch.softmax(emotion_logits, dim=1)
        
        # Detect sarcasm
        sarcasm_score = self._detect_sarcasm(clean_text, sentiment_probs[0])
        
        return {
            'text': original_text[:200] + '...' if len(original_text) > 200 else original_text,
            'language': language,
            'sentiment': {
                'label': self.SENTIMENT_LABELS[sentiment_idx],
                'score': sentiment_probs[0][sentiment_idx].item(),
                'confidence': sentiment_probs[0][sentiment_idx].item(),
                'distribution': {
                    label: prob.item()
                    for label, prob in zip(self.SENTIMENT_LABELS, sentiment_probs[0])
                }
            },
            'emotions': self._get_top_emotions(emotion_probs[0]),
            'sarcasm': {
                'detected': sarcasm_score > 0.7,
                'score': sarcasm_score
            },
            'intensity': self._calculate_intensity(sentiment_probs, emotion_probs),
            'model': 'bert'
        }
    
    def _analyze_textblob(self, original_text: str, clean_text: str, language: str) -> Dict:
        """Analyze using TextBlob"""
        blob = TextBlob(clean_text if clean_text else original_text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1
        
        # Classify sentiment
        if polarity > 0.1:
            sentiment_label = 'positive'
        elif polarity < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Convert polarity to probabilities
        if polarity > 0:
            pos_prob = 0.5 + (polarity * 0.5)
            neg_prob = (1 - pos_prob) * 0.3
            neu_prob = 1 - pos_prob - neg_prob
        elif polarity < 0:
            neg_prob = 0.5 + (abs(polarity) * 0.5)
            pos_prob = (1 - neg_prob) * 0.3
            neu_prob = 1 - pos_prob - neg_prob
        else:
            pos_prob = 0.33
            neg_prob = 0.33
            neu_prob = 0.34
        
        # Basic sarcasm detection
        sarcasm_score = self._detect_sarcasm_basic(clean_text)
        
        return {
            'text': original_text[:200] + '...' if len(original_text) > 200 else original_text,
            'language': language,
            'sentiment': {
                'label': sentiment_label,
                'score': abs(polarity),
                'confidence': abs(polarity),
                'polarity': polarity,
                'subjectivity': subjectivity,
                'distribution': {
                    'negative': neg_prob,
                    'neutral': neu_prob,
                    'positive': pos_prob
                }
            },
            'sarcasm': {
                'detected': sarcasm_score > 0.5,
                'score': sarcasm_score
            },
            'model': 'textblob'
        }
    
    def _analyze_basic(self, original_text: str, clean_text: str, language: str) -> Dict:
        """Basic keyword-based sentiment analysis"""
        positive_words = ['good', 'great', 'amazing', 'love', 'excellent', 'happy', 
                         'wonderful', 'fantastic', 'best', 'awesome', 'thank', 'beautiful',
                         'perfect', 'nice', 'like', 'enjoy', 'pleased']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'worst', 'sad', 
                         'disappointed', 'angry', 'horrible', 'poor', 'wrong', 'ugly',
                         'fail', 'useless', 'annoying', 'frustrating']
        
        text_lower = clean_text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            sentiment_label = 'neutral'
            score = 0.5
        elif pos_count > neg_count:
            sentiment_label = 'positive'
            score = pos_count / (total + 1)
        else:
            sentiment_label = 'negative'
            score = neg_count / (total + 1)
        
        return {
            'text': original_text[:200] + '...' if len(original_text) > 200 else original_text,
            'language': language,
            'sentiment': {
                'label': sentiment_label,
                'score': min(score, 1.0),
                'confidence': min(score, 1.0)
            },
            'model': 'basic'
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove mentions (but keep for context)
        text = re.sub(r'@\w+', '', text)
        
        # Convert hashtags to words
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _detect_sarcasm(self, text: str, sentiment_probs) -> float:
        """Detect sarcasm using linguistic patterns and sentiment contradiction"""
        text_lower = text.lower()
        
        # Check for sarcasm indicators
        indicator_count = sum(1 for ind in self.sarcasm_indicators if ind in text_lower)
        
        # Check for punctuation patterns
        has_exclamation = '!' in text
        has_ellipsis = '...' in text
        has_quotes = '"' in text or "'" in text
        
        # Calculate sarcasm score
        sarcasm_score = 0.0
        
        if indicator_count > 0:
            sarcasm_score += 0.25 * min(indicator_count, 3)
        
        if has_exclamation and sentiment_probs[0].item() > 0.3:  # Negative with exclamation
            sarcasm_score += 0.3
        
        if has_ellipsis:
            sarcasm_score += 0.15
        
        if has_quotes:
            sarcasm_score += 0.1
        
        return min(sarcasm_score, 1.0)
    
    def _detect_sarcasm_basic(self, text: str) -> float:
        """Basic sarcasm detection without neural network"""
        text_lower = text.lower()
        
        indicator_count = sum(1 for ind in self.sarcasm_indicators if ind in text_lower)
        has_exclamation = text.count('!') > 1
        has_ellipsis = '...' in text
        has_caps = sum(1 for c in text if c.isupper()) > len(text) * 0.3
        
        score = 0.0
        if indicator_count > 0:
            score += 0.3 * min(indicator_count, 3)
        if has_exclamation:
            score += 0.2
        if has_ellipsis:
            score += 0.15
        if has_caps and len(text) > 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_intensity(self, sentiment_probs, emotion_probs) -> float:
        """Calculate overall emotional intensity"""
        import numpy as np
        
        # Use entropy to measure intensity
        sentiment_entropy = -torch.sum(sentiment_probs * torch.log(sentiment_probs + 1e-10))
        emotion_entropy = -torch.sum(emotion_probs * torch.log(emotion_probs + 1e-10))
        
        # Lower entropy = higher intensity (more confident)
        max_sentiment_entropy = np.log(3)
        max_emotion_entropy = np.log(8)
        
        sentiment_intensity = 1 - (sentiment_entropy.item() / max_sentiment_entropy)
        emotion_intensity = 1 - (emotion_entropy.item() / max_emotion_entropy)
        
        return (sentiment_intensity + emotion_intensity) / 2
    
    def _get_top_emotions(self, emotion_probs, k: int = 3) -> List[Dict]:
        """Get top k emotions with scores"""
        top_k = torch.topk(emotion_probs, k=min(k, len(self.EMOTION_LABELS)))
        
        return [
            {
                'emotion': self.EMOTION_LABELS[idx.item()],
                'score': score.item()
            }
            for idx, score in zip(top_k.indices, top_k.values)
        ]
    
    def _empty_result(self, text: str, language: str) -> Dict:
        """Return empty/neutral result for empty text"""
        return {
            'text': text,
            'language': language,
            'sentiment': {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            },
            'model': 'none'
        }
    
    def _load_weights(self):
        """Load pre-trained weights if available"""
        weights_path = self.models_dir / 'advanced_sentiment_model.pth'
        try:
            if weights_path.exists():
                checkpoint = torch.load(weights_path, map_location=self.device)
                self.sentiment_classifier.load_state_dict(checkpoint['sentiment_classifier'])
                self.emotion_classifier.load_state_dict(checkpoint['emotion_classifier'])
                print(f"✓ Loaded pre-trained weights from {weights_path}")
        except Exception as e:
            print(f"ℹ No pre-trained weights loaded: {e}")
    
    def save_model(self, path: Optional[str] = None):
        """Save model weights"""
        if not self.use_bert:
            print("⚠ No BERT model to save")
            return
        
        save_path = Path(path) if path else self.models_dir / 'advanced_sentiment_model.pth'
        torch.save({
            'sentiment_classifier': self.sentiment_classifier.state_dict(),
            'emotion_classifier': self.emotion_classifier.state_dict()
        }, save_path)
        print(f"✓ Model saved to {save_path}")


# Singleton instance
_analyzer_instance: Optional[AdvancedSentimentAnalyzer] = None


def get_advanced_analyzer() -> AdvancedSentimentAnalyzer:
    """Get or create singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = AdvancedSentimentAnalyzer()
    return _analyzer_instance
