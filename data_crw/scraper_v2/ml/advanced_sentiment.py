"""
Advanced Sentiment Analyzer v2.0
================================
Advanced ML-based sentiment analysis with BERT support.

Features:
- BERT-based sentiment analysis
- Multi-language support
- Zero-shot classification
- Entity recognition
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

# Check for PyTorch and Transformers
HAS_TRANSFORMERS = False
HAS_TORCH = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    logger.info("PyTorch not installed. Advanced sentiment will be limited.")
    
try:
    from transformers import (
        pipeline,
        AutoModelForSequenceClassification,
        AutoTokenizer,
    )
    HAS_TRANSFORMERS = True
except ImportError:
    logger.info("Transformers not installed. Advanced sentiment will be limited.")


class AdvancedSentimentAnalyzer:
    """
    Advanced sentiment analysis using BERT/Transformer models.
    
    Falls back to TextBlob if transformers not available.
    """
    
    # Default model configurations
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    MULTILINGUAL_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"
    ZERO_SHOT_MODEL = "facebook/bart-large-mnli"
    NER_MODEL = "dbmdz/bert-large-cased-finetuned-conll03-english"
    
    def __init__(
        self,
        use_gpu: bool = True,
        model_name: Optional[str] = None,
        cache_models: bool = True,
    ):
        """
        Initialize Advanced Sentiment Analyzer.
        
        Args:
            use_gpu: Use GPU if available
            model_name: Custom model name (optional)
            cache_models: Cache loaded models
        """
        self.use_gpu = use_gpu and HAS_TORCH and torch.cuda.is_available()
        self.device = 0 if self.use_gpu else -1
        self.model_name = model_name or self.SENTIMENT_MODEL
        self.cache_models = cache_models
        
        # Model cache
        self._sentiment_pipeline = None
        self._zero_shot_pipeline = None
        self._ner_pipeline = None
        
        # Fallback analyzer
        self._fallback = None
        
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available. Using fallback analyzer.")
            self._init_fallback()
            
    def _init_fallback(self):
        """Initialize fallback analyzer."""
        try:
            from .analyzer import DataAnalyzer
            self._fallback = DataAnalyzer()
        except ImportError:
            logger.error("Cannot import fallback analyzer")
            
    def _get_sentiment_pipeline(self):
        """Get or create sentiment pipeline."""
        if self._sentiment_pipeline is None and HAS_TRANSFORMERS:
            try:
                self._sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    device=self.device,
                )
            except Exception as e:
                logger.error(f"Failed to load sentiment model: {e}")
                self._init_fallback()
        return self._sentiment_pipeline
        
    def _get_zero_shot_pipeline(self):
        """Get or create zero-shot classification pipeline."""
        if self._zero_shot_pipeline is None and HAS_TRANSFORMERS:
            try:
                self._zero_shot_pipeline = pipeline(
                    "zero-shot-classification",
                    model=self.ZERO_SHOT_MODEL,
                    device=self.device,
                )
            except Exception as e:
                logger.error(f"Failed to load zero-shot model: {e}")
        return self._zero_shot_pipeline
        
    def _get_ner_pipeline(self):
        """Get or create NER pipeline."""
        if self._ner_pipeline is None and HAS_TRANSFORMERS:
            try:
                self._ner_pipeline = pipeline(
                    "ner",
                    model=self.NER_MODEL,
                    device=self.device,
                    aggregation_strategy="simple",
                )
            except Exception as e:
                logger.error(f"Failed to load NER model: {e}")
        return self._ner_pipeline
        
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using BERT model.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text or not text.strip():
            return {
                'label': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'model': 'none',
            }
            
        # Truncate long texts
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]
            
        pipeline = self._get_sentiment_pipeline()
        
        if pipeline is None:
            # Use fallback
            if self._fallback:
                result = self._fallback.analyze_sentiment(text)
                result['model'] = 'fallback'
                return result
            return {'label': 'neutral', 'score': 0.0, 'model': 'none'}
            
        try:
            result = pipeline(text)[0]
            
            # Normalize label
            label = result['label'].lower()
            if 'positive' in label or 'pos' in label:
                label = 'positive'
            elif 'negative' in label or 'neg' in label:
                label = 'negative'
            else:
                label = 'neutral'
                
            return {
                'label': label,
                'score': result['score'] if label == 'positive' else -result['score'],
                'confidence': result['score'],
                'raw_label': result['label'],
                'model': self.model_name,
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            if self._fallback:
                result = self._fallback.analyze_sentiment(text)
                result['model'] = 'fallback'
                return result
            return {'label': 'neutral', 'score': 0.0, 'model': 'error'}
            
    def analyze_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of texts
            batch_size: Processing batch size
            
        Returns:
            List of sentiment results
        """
        results = []
        
        pipeline = self._get_sentiment_pipeline()
        
        if pipeline is None:
            return [self.analyze(text) for text in texts]
            
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Clean and truncate
            batch = [
                (t[:512] if len(t) > 512 else t) if t else ""
                for t in batch
            ]
            
            try:
                batch_results = pipeline(batch)
                for result in batch_results:
                    label = result['label'].lower()
                    if 'positive' in label:
                        label = 'positive'
                    elif 'negative' in label:
                        label = 'negative'
                    else:
                        label = 'neutral'
                    results.append({
                        'label': label,
                        'score': result['score'] if label == 'positive' else -result['score'],
                        'confidence': result['score'],
                    })
            except Exception as e:
                logger.error(f"Batch analysis failed: {e}")
                results.extend([self.analyze(t) for t in batch])
                
        return results
        
    def classify(self, text: str, labels: List[str]) -> Dict[str, Any]:
        """
        Zero-shot classification.
        
        Args:
            text: Text to classify
            labels: Candidate labels
            
        Returns:
            Classification result
        """
        if not text or not labels:
            return {'label': None, 'scores': {}}
            
        pipeline = self._get_zero_shot_pipeline()
        
        if pipeline is None:
            return {'label': labels[0] if labels else None, 'scores': {}}
            
        try:
            result = pipeline(text, labels)
            return {
                'label': result['labels'][0],
                'score': result['scores'][0],
                'all_labels': result['labels'],
                'all_scores': result['scores'],
                'scores': dict(zip(result['labels'], result['scores'])),
            }
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {'label': None, 'scores': {}}
            
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entities
        """
        if not text:
            return []
            
        pipeline = self._get_ner_pipeline()
        
        if pipeline is None:
            # Simple fallback - extract capitalized words
            entities = []
            words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
            for word in words:
                entities.append({
                    'entity': 'UNKNOWN',
                    'word': word,
                    'score': 0.5,
                })
            return entities
            
        try:
            results = pipeline(text)
            return [
                {
                    'entity': r['entity_group'],
                    'word': r['word'],
                    'score': r['score'],
                    'start': r['start'],
                    'end': r['end'],
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
            
    def analyze_comments_advanced(
        self,
        comments: List[Dict],
        include_entities: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive comment analysis.
        
        Args:
            comments: List of comment dictionaries
            include_entities: Whether to extract entities
            
        Returns:
            Comprehensive analysis
        """
        if not comments:
            return {
                'total': 0,
                'sentiments': [],
                'summary': {},
            }
            
        texts = [c.get('text', '') for c in comments if c.get('text')]
        
        # Batch sentiment analysis
        sentiments = self.analyze_batch(texts)
        
        # Count distribution
        distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        for s in sentiments:
            distribution[s['label']] += 1
            
        result = {
            'total': len(comments),
            'analyzed': len(sentiments),
            'sentiments': sentiments,
            'distribution': distribution,
            'avg_score': sum(s['score'] for s in sentiments) / len(sentiments) if sentiments else 0,
        }
        
        # Extract entities if requested
        if include_entities:
            all_entities = []
            for text in texts[:50]:  # Limit for performance
                entities = self.extract_entities(text)
                all_entities.extend(entities)
            result['entities'] = all_entities
            
        return result
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            'has_transformers': HAS_TRANSFORMERS,
            'has_torch': HAS_TORCH,
            'gpu_available': HAS_TORCH and torch.cuda.is_available(),
            'using_gpu': self.use_gpu,
            'sentiment_model': self.model_name,
            'models_cached': {
                'sentiment': self._sentiment_pipeline is not None,
                'zero_shot': self._zero_shot_pipeline is not None,
                'ner': self._ner_pipeline is not None,
            },
        }
