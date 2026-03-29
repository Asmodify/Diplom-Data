"""
AI-Powered Data Analyzer v2.0
==============================
Comprehensive analysis of scraped Facebook data using AI/ML techniques.
Provides insights, patterns, trends, and actionable recommendations.

Features:
- TF-IDF topic extraction and clustering
- Comprehensive sentiment analysis
- Engagement metrics analysis
- Temporal pattern detection
- Viral potential calculation
- Automated recommendations generation
- Community health assessment
"""

import json
import logging
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Import ML modules
try:
    from .analyzer import DataAnalyzer
    from .advanced_sentiment import AdvancedSentimentAnalyzer
except ImportError:
    from analyzer import DataAnalyzer
    from advanced_sentiment import AdvancedSentimentAnalyzer

# Optional imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.info("NumPy not installed. Some features will be limited.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.info("scikit-learn not installed. Topic clustering will be limited.")


class AIAnalyzer:
    """
    AI-powered comprehensive analyzer for Facebook scraper data.
    Analyzes posts, comments, and engagement metrics to provide insights.
    
    Features:
    - Content analysis (length, hashtags, mentions, content types)
    - Sentiment analysis (TextBlob, VADER, BERT)
    - Engagement metrics analysis
    - Temporal pattern detection
    - Topic clustering with TF-IDF and KMeans
    - Audience behavior analysis
    - Automated recommendations
    """
    
    def __init__(self, config=None, models_dir: Optional[str] = None):
        """
        Initialize the AI Analyzer.
        
        Args:
            config: Configuration object (uses defaults if None)
            models_dir: Directory for model storage
        """
        if config is None:
            try:
                from config import get_config
                config = get_config()
            except ImportError:
                config = None
                
        self.config = config
        
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            self.models_dir = Path(__file__).parent.parent / 'models'
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize sub-analyzers
        self.data_analyzer = DataAnalyzer(config)
        self.sentiment_analyzer = AdvancedSentimentAnalyzer()
        
        logger.info("AI Analyzer initialized")
    
    def analyze_all(
        self,
        posts: List[Dict],
        comments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive AI analysis of all scraped data.
        
        Args:
            posts: List of scraped posts
            comments: List of scraped comments (optional)
        
        Returns:
            Complete analysis report with metadata, sentiment, engagement,
            temporal patterns, topics, audience insights, and recommendations
        """
        if not posts:
            return {
                "error": "No data to analyze",
                "timestamp": datetime.now().isoformat()
            }
        
        comments = comments or []
        
        analysis = {
            "metadata": self._generate_metadata(posts, comments),
            "content_analysis": self._analyze_content(posts, comments),
            "sentiment_analysis": self._analyze_sentiment(posts, comments),
            "engagement_analysis": self._analyze_engagement(posts),
            "temporal_analysis": self._analyze_temporal_patterns(posts),
            "topic_analysis": self._analyze_topics(posts, comments),
            "audience_insights": self._analyze_audience(comments),
            "recommendations": [],
            "ai_summary": ""
        }
        
        # Generate AI recommendations based on analysis
        analysis["recommendations"] = self._generate_recommendations(analysis)
        analysis["ai_summary"] = self._generate_ai_summary(analysis)
        
        return analysis
    
    def _generate_metadata(
        self,
        posts: List[Dict],
        comments: List[Dict]
    ) -> Dict[str, Any]:
        """Generate analysis metadata."""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_posts": len(posts),
            "total_comments": len(comments),
            "date_range": self._get_date_range(posts),
            "pages_analyzed": len(set(
                p.get('page_name') or p.get('page_id') or 'Unknown'
                for p in posts
            )),
            "analysis_version": "2.0.0"
        }
    
    def _get_date_range(self, posts: List[Dict]) -> Dict[str, Any]:
        """Get date range of posts."""
        dates = []
        for post in posts:
            date_str = (
                post.get('date') or
                post.get('post_date') or
                post.get('created_at') or
                post.get('scraped_at')
            )
            if date_str:
                try:
                    if isinstance(date_str, datetime):
                        dates.append(date_str)
                    elif isinstance(date_str, str):
                        for fmt in [
                            '%Y-%m-%d',
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                            '%B %d, %Y'
                        ]:
                            try:
                                dates.append(datetime.strptime(date_str, fmt))
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass
        
        if dates:
            return {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat(),
                "span_days": (max(dates) - min(dates)).days
            }
        return {"earliest": None, "latest": None, "span_days": 0}
    
    def _analyze_content(
        self,
        posts: List[Dict],
        comments: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze content characteristics."""
        post_texts = [
            p.get('content') or p.get('text') or ''
            for p in posts
        ]
        comment_texts = [
            c.get('text') or c.get('comment_text') or c.get('content') or ''
            for c in comments
        ]
        
        # Post content analysis
        post_lengths = [len(t) for t in post_texts if t]
        word_counts = [len(t.split()) for t in post_texts if t]
        
        # Extract hashtags and mentions
        all_hashtags = []
        all_mentions = []
        for text in post_texts + comment_texts:
            if text:
                all_hashtags.extend(re.findall(r'#(\w+)', text))
                all_mentions.extend(re.findall(r'@(\w+)', text))
        
        # Detect content types
        content_types = Counter()
        for post in posts:
            if post.get('video_url') or post.get('has_video'):
                content_types['video'] += 1
            elif post.get('image_urls') or post.get('image_url') or post.get('has_image'):
                content_types['image'] += 1
            elif post.get('link_url') or post.get('url'):
                content_types['link'] += 1
            else:
                content_types['text'] += 1
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = []
        for text in post_texts:
            if text:
                urls.extend(re.findall(url_pattern, text))
        
        return {
            "post_statistics": {
                "avg_length_chars": round(
                    statistics.mean(post_lengths), 1
                ) if post_lengths else 0,
                "avg_word_count": round(
                    statistics.mean(word_counts), 1
                ) if word_counts else 0,
                "max_length": max(post_lengths) if post_lengths else 0,
                "min_length": min(post_lengths) if post_lengths else 0
            },
            "comment_statistics": {
                "avg_length_chars": round(
                    statistics.mean([len(t) for t in comment_texts if t]), 1
                ) if any(comment_texts) else 0,
                "total_words": sum(len(t.split()) for t in comment_texts if t)
            },
            "hashtags": {
                "total_count": len(all_hashtags),
                "unique_count": len(set(all_hashtags)),
                "top_10": Counter(all_hashtags).most_common(10)
            },
            "mentions": {
                "total_count": len(all_mentions),
                "unique_count": len(set(all_mentions)),
                "top_10": Counter(all_mentions).most_common(10)
            },
            "content_types": dict(content_types),
            "urls_found": len(urls),
            "unique_domains": len(set(
                re.findall(r'https?://([^/]+)', ' '.join(urls))
            ))
        }
    
    def _analyze_sentiment(
        self,
        posts: List[Dict],
        comments: List[Dict]
    ) -> Dict[str, Any]:
        """Comprehensive sentiment analysis."""
        post_texts = [
            p.get('content') or p.get('text') or ''
            for p in posts
            if p.get('content') or p.get('text')
        ]
        comment_texts = [
            c.get('text') or c.get('comment_text') or c.get('content') or ''
            for c in comments
            if c.get('text') or c.get('comment_text') or c.get('content')
        ]
        
        # Analyze posts sentiment (limit for performance)
        post_sentiments = []
        for text in post_texts[:100]:
            try:
                result = self.sentiment_analyzer.analyze(text)
                post_sentiments.append(result)
            except Exception as e:
                logger.debug(f"Sentiment analysis error: {e}")
        
        # Analyze comments sentiment (limit for performance)
        comment_sentiments = []
        for text in comment_texts[:500]:
            try:
                result = self.sentiment_analyzer.analyze(text)
                comment_sentiments.append(result)
            except Exception as e:
                logger.debug(f"Sentiment analysis error: {e}")
        
        def aggregate_sentiments(sentiments: List[Dict]) -> Dict[str, Any]:
            if not sentiments:
                return {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "avg_confidence": 0,
                    "total_analyzed": 0
                }
            
            positive = sum(
                1 for s in sentiments
                if s.get('label') == 'positive' or s.get('sentiment') == 'positive'
            )
            negative = sum(
                1 for s in sentiments
                if s.get('label') == 'negative' or s.get('sentiment') == 'negative'
            )
            neutral = sum(
                1 for s in sentiments
                if s.get('label') == 'neutral' or s.get('sentiment') == 'neutral'
            )
            scores = [
                s.get('confidence') or s.get('score') or 0.5
                for s in sentiments
            ]
            
            total = len(sentiments)
            return {
                "positive": round(positive / total * 100, 1),
                "negative": round(negative / total * 100, 1),
                "neutral": round(neutral / total * 100, 1),
                "avg_confidence": round(
                    statistics.mean(scores) * 100, 1
                ) if scores else 0,
                "total_analyzed": total
            }
        
        return {
            "overall_sentiment": self._calculate_overall_sentiment(
                post_sentiments + comment_sentiments
            ),
            "post_sentiment": aggregate_sentiments(post_sentiments),
            "comment_sentiment": aggregate_sentiments(comment_sentiments),
            "sentiment_trend": self._calculate_sentiment_trend(
                posts, post_sentiments
            ),
            "toxicity_indicators": self._detect_toxicity(comment_texts)
        }
    
    def _calculate_overall_sentiment(self, sentiments: List[Dict]) -> str:
        """Calculate overall sentiment label."""
        if not sentiments:
            return "neutral"
        
        positive = sum(
            1 for s in sentiments
            if s.get('label') == 'positive' or s.get('sentiment') == 'positive'
        )
        negative = sum(
            1 for s in sentiments
            if s.get('label') == 'negative' or s.get('sentiment') == 'negative'
        )
        
        if positive > negative * 1.5:
            return "mostly_positive"
        elif negative > positive * 1.5:
            return "mostly_negative"
        elif positive > negative:
            return "slightly_positive"
        elif negative > positive:
            return "slightly_negative"
        return "neutral"
    
    def _calculate_sentiment_trend(
        self,
        posts: List[Dict],
        sentiments: List[Dict]
    ) -> str:
        """Detect sentiment trend over time."""
        if len(sentiments) < 5:
            return "insufficient_data"
        
        mid = len(sentiments) // 2
        first_half = sentiments[:mid]
        second_half = sentiments[mid:]
        
        def get_positive_rate(sents):
            pos = sum(
                1 for s in sents
                if s.get('label') == 'positive' or s.get('sentiment') == 'positive'
            )
            return pos / len(sents) if sents else 0
        
        first_positive = get_positive_rate(first_half)
        second_positive = get_positive_rate(second_half)
        
        diff = second_positive - first_positive
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"
    
    def _detect_toxicity(self, texts: List[str]) -> Dict[str, Any]:
        """Detect potentially toxic content."""
        toxic_patterns = [
            r'\b(hate|stupid|idiot|dumb|loser|trash)\b',
            r'\b(kill|die|death|destroy)\b',
            r'[!?]{3,}',
            r'[A-Z]{5,}'
        ]
        
        toxic_count = 0
        aggressive_count = 0
        
        for text in texts:
            if not text:
                continue
            text_lower = text.lower()
            for pattern in toxic_patterns[:2]:
                if re.search(pattern, text_lower):
                    toxic_count += 1
                    break
            for pattern in toxic_patterns[2:]:
                if re.search(pattern, text):
                    aggressive_count += 1
                    break
        
        total = len([t for t in texts if t])
        return {
            "potentially_toxic": toxic_count,
            "aggressive_tone": aggressive_count,
            "toxicity_rate": round(
                toxic_count / total * 100, 2
            ) if total else 0,
            "total_analyzed": total
        }
    
    def _analyze_engagement(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement metrics."""
        likes = [int(p.get('likes') or 0) for p in posts]
        comments = [
            int(p.get('comments_count') or p.get('comments') or 0)
            for p in posts
        ]
        shares = [int(p.get('shares') or 0) for p in posts]
        
        total_engagement = sum(likes) + sum(comments) + sum(shares)
        avg_engagement = total_engagement / len(posts) if posts else 0
        
        # Find top performing posts
        engagement_scores = []
        for i, post in enumerate(posts):
            score = (
                int(post.get('likes') or 0) +
                int(post.get('comments_count') or post.get('comments') or 0) * 2 +
                int(post.get('shares') or 0) * 3
            )
            engagement_scores.append((i, score, post))
        
        top_posts = sorted(
            engagement_scores,
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_engagement": total_engagement,
            "avg_engagement_per_post": round(avg_engagement, 1),
            "likes": {
                "total": sum(likes),
                "average": round(statistics.mean(likes), 1) if likes else 0,
                "max": max(likes) if likes else 0,
                "std_dev": round(
                    statistics.stdev(likes), 1
                ) if len(likes) > 1 else 0
            },
            "comments": {
                "total": sum(comments),
                "average": round(statistics.mean(comments), 1) if comments else 0,
                "max": max(comments) if comments else 0
            },
            "shares": {
                "total": sum(shares),
                "average": round(statistics.mean(shares), 1) if shares else 0,
                "max": max(shares) if shares else 0
            },
            "engagement_rate": round(avg_engagement / 1000 * 100, 2),
            "top_performing_posts": [
                {
                    "index": tp[0],
                    "score": tp[1],
                    "preview": (
                        tp[2].get('content') or tp[2].get('text') or ''
                    )[:100]
                }
                for tp in top_posts
            ],
            "viral_potential": self._calculate_viral_potential(posts)
        }
    
    def _calculate_viral_potential(self, posts: List[Dict]) -> Dict[str, Any]:
        """Calculate viral potential based on engagement patterns."""
        if not posts:
            return {"score": 0, "classification": "low"}
        
        high_engagement = 0
        for post in posts:
            engagement = (
                int(post.get('likes') or 0) +
                int(post.get('shares') or 0) * 2
            )
            if engagement > 1000:
                high_engagement += 1
        
        rate = high_engagement / len(posts)
        if rate > 0.3:
            return {"score": round(rate * 100, 1), "classification": "high"}
        elif rate > 0.1:
            return {"score": round(rate * 100, 1), "classification": "medium"}
        return {"score": round(rate * 100, 1), "classification": "low"}
    
    def _analyze_temporal_patterns(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze posting patterns over time."""
        hourly_distribution = Counter()
        daily_distribution = Counter()
        
        for post in posts:
            date_str = (
                post.get('date') or
                post.get('post_date') or
                post.get('created_at')
            )
            if date_str:
                try:
                    if isinstance(date_str, datetime):
                        hourly_distribution[date_str.hour] += 1
                        daily_distribution[date_str.strftime('%A')] += 1
                    elif isinstance(date_str, str) and ':' in date_str:
                        parts = date_str.split()
                        for part in parts:
                            if ':' in part:
                                hour = int(part.split(':')[0])
                                hourly_distribution[hour] += 1
                                break
                except Exception:
                    pass
        
        best_hours = sorted(
            hourly_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        date_range = self._get_date_range(posts)
        span_days = date_range.get('span_days') or 1
        
        return {
            "hourly_distribution": dict(sorted(hourly_distribution.items())),
            "daily_distribution": dict(daily_distribution),
            "best_posting_hours": [h[0] for h in best_hours],
            "posting_frequency": {
                "posts_per_day": round(len(posts) / max(1, span_days), 2)
            }
        }
    
    def _analyze_topics(
        self,
        posts: List[Dict],
        comments: List[Dict]
    ) -> Dict[str, Any]:
        """Extract and analyze topics using NLP."""
        all_texts = [
            p.get('content') or p.get('text') or ''
            for p in posts
        ]
        all_texts += [
            c.get('text') or c.get('comment_text') or c.get('content') or ''
            for c in comments
        ]
        all_texts = [t for t in all_texts if t and len(t) > 20]
        
        if not all_texts:
            return {"topics": [], "top_keywords": [], "dominant_themes": []}
        
        if not SKLEARN_AVAILABLE:
            return {
                "topics": [],
                "top_keywords": [],
                "dominant_themes": [],
                "note": "Install scikit-learn for topic analysis"
            }
        
        try:
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Extract top keywords
            feature_names = vectorizer.get_feature_names_out()
            mean_tfidf = tfidf_matrix.mean(axis=0).A1
            top_indices = mean_tfidf.argsort()[-20:][::-1]
            keywords: List[Tuple[str, float]] = [
                (str(feature_names[i]), float(round(mean_tfidf[i], 4)))
                for i in top_indices
            ]
            
            # Topic clustering
            n_clusters = min(5, len(all_texts) // 10 + 1)
            topics = []
            
            if n_clusters >= 2:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(tfidf_matrix)
                
                for i in range(n_clusters):
                    cluster_center = kmeans.cluster_centers_[i]
                    top_word_indices = cluster_center.argsort()[-5:][::-1]
                    topic_words = [feature_names[idx] for idx in top_word_indices]
                    topics.append({
                        "id": i,
                        "keywords": topic_words,
                        "size": int(sum(clusters == i))
                    })
            
            return {
                "topics": topics,
                "top_keywords": keywords[:15],
                "keyword_diversity": len(set(feature_names)),
                "dominant_themes": self._identify_themes(keywords)
            }
            
        except Exception as e:
            logger.error(f"Topic analysis error: {e}")
            return {"topics": [], "top_keywords": [], "error": str(e)}
    
    def _identify_themes(
        self,
        keywords: List[Tuple[str, float]]
    ) -> List[str]:
        """Identify dominant themes from keywords."""
        theme_keywords = {
            "politics": ["government", "election", "president", "policy", "vote"],
            "technology": ["tech", "software", "app", "digital", "online"],
            "business": ["company", "business", "market", "price", "money"],
            "entertainment": ["movie", "music", "show", "celebrity", "fun"],
            "sports": ["game", "team", "player", "win", "score"],
            "health": ["health", "covid", "medical", "doctor", "vaccine"]
        }
        
        detected_themes = []
        keyword_words = [k[0].lower() for k in keywords]
        
        for theme, words in theme_keywords.items():
            if any(w in kw for kw in keyword_words for w in words):
                detected_themes.append(theme)
        
        return detected_themes if detected_themes else ["general"]
    
    def _analyze_audience(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze audience behavior from comments."""
        if not comments:
            return {
                "engagement_level": "unknown",
                "unique_authors": 0,
                "total_interactions": 0
            }
        
        authors = [
            c.get('author') or c.get('author_name') or ''
            for c in comments
        ]
        authors = [a for a in authors if a]
        
        unique_authors = len(set(authors))
        total_comments = len(comments)
        
        comments_per_author = (
            total_comments / unique_authors if unique_authors else 0
        )
        
        if comments_per_author > 3:
            engagement_level = "highly_engaged"
        elif comments_per_author > 1.5:
            engagement_level = "moderately_engaged"
        else:
            engagement_level = "lightly_engaged"
        
        author_counts = Counter(authors)
        top_commenters = author_counts.most_common(10)
        
        return {
            "unique_authors": unique_authors,
            "total_interactions": total_comments,
            "avg_comments_per_author": round(comments_per_author, 2),
            "engagement_level": engagement_level,
            "top_commenters": [
                {"author": a, "count": c}
                for a, c in top_commenters
            ],
            "community_health": self._assess_community_health(comments)
        }
    
    def _assess_community_health(self, comments: List[Dict]) -> Dict[str, Any]:
        """Assess overall community health."""
        if not comments:
            return {"score": 0, "status": "unknown"}
        
        total = len(comments)
        
        # Check for conversation threads (replies)
        replies = sum(
            1 for c in comments
            if c.get('reply_to') or c.get('parent_id') or c.get('parent_comment_id')
        )
        reply_rate = replies / total if total else 0
        
        # Positive vs negative interactions
        positive_indicators = sum(
            1 for c in comments
            if any(
                word in (
                    c.get('text') or c.get('comment_text') or ''
                ).lower()
                for word in ['thanks', 'great', 'love', 'awesome', 'agree']
            )
        )
        
        positivity_rate = positive_indicators / total if total else 0
        
        score = (reply_rate * 30) + (positivity_rate * 70)
        
        if score > 50:
            status = "healthy"
        elif score > 25:
            status = "moderate"
        else:
            status = "needs_attention"
        
        return {
            "score": round(score, 1),
            "status": status,
            "reply_rate": round(reply_rate * 100, 1),
            "positivity_rate": round(positivity_rate * 100, 1)
        }
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations based on analysis."""
        recommendations = []
        
        # Sentiment-based recommendations
        sentiment = analysis.get('sentiment_analysis', {})
        overall = sentiment.get('overall_sentiment', '')
        if overall in ['mostly_negative', 'slightly_negative']:
            recommendations.append({
                "category": "content_strategy",
                "priority": "high",
                "recommendation": (
                    "Sentiment is trending negative. "
                    "Consider more positive, uplifting content."
                ),
                "action": (
                    "Review recent posts and identify topics "
                    "causing negative reactions"
                )
            })
        
        # Engagement-based recommendations
        engagement = analysis.get('engagement_analysis', {})
        if engagement.get('engagement_rate', 0) < 2:
            recommendations.append({
                "category": "engagement",
                "priority": "high",
                "recommendation": (
                    "Engagement rate is below average. "
                    "Try more interactive content."
                ),
                "action": "Add questions, polls, or call-to-actions to posts"
            })
        
        # Temporal recommendations
        temporal = analysis.get('temporal_analysis', {})
        best_hours = temporal.get('best_posting_hours', [])
        if best_hours:
            recommendations.append({
                "category": "timing",
                "priority": "medium",
                "recommendation": f"Best posting times detected: {best_hours}",
                "action": (
                    f"Schedule important content around {best_hours[0]}:00 "
                    "for maximum reach"
                )
            })
        
        # Content recommendations
        content = analysis.get('content_analysis', {})
        avg_length = content.get('post_statistics', {}).get('avg_length_chars', 0)
        if avg_length > 500:
            recommendations.append({
                "category": "content_format",
                "priority": "low",
                "recommendation": (
                    "Posts are quite long. "
                    "Consider shorter, more digestible content."
                ),
                "action": "Aim for 100-280 characters for better engagement"
            })
        
        # Topic recommendations
        topics = analysis.get('topic_analysis', {})
        if topics.get('top_keywords'):
            top_kw = [k[0] for k in topics['top_keywords'][:5]]
            recommendations.append({
                "category": "content_focus",
                "priority": "medium",
                "recommendation": f"Trending topics: {', '.join(top_kw)}",
                "action": "Create more content around these popular keywords"
            })
        
        # Toxicity recommendations
        toxicity = sentiment.get('toxicity_indicators', {})
        if toxicity.get('toxicity_rate', 0) > 5:
            recommendations.append({
                "category": "moderation",
                "priority": "high",
                "recommendation": "Elevated toxicity levels detected in comments.",
                "action": (
                    "Consider implementing stricter moderation "
                    "or community guidelines"
                )
            })
        
        return recommendations
    
    def _generate_ai_summary(self, analysis: Dict) -> str:
        """Generate human-readable AI summary."""
        metadata = analysis.get('metadata', {})
        sentiment = analysis.get('sentiment_analysis', {})
        engagement = analysis.get('engagement_analysis', {})
        topics = analysis.get('topic_analysis', {})
        
        summary_parts = []
        
        # Overview
        summary_parts.append(
            f"Analysis of {metadata.get('total_posts', 0)} posts and "
            f"{metadata.get('total_comments', 0)} comments from "
            f"{metadata.get('pages_analyzed', 0)} Facebook page(s)."
        )
        
        # Sentiment summary
        overall = sentiment.get('overall_sentiment', 'neutral')
        post_sent = sentiment.get('post_sentiment', {})
        summary_parts.append(
            f"Overall sentiment is {overall.replace('_', ' ')}. "
            f"Post sentiment: {post_sent.get('positive', 0)}% positive, "
            f"{post_sent.get('negative', 0)}% negative."
        )
        
        # Engagement summary
        summary_parts.append(
            f"Total engagement: {engagement.get('total_engagement', 0):,} interactions. "
            f"Average engagement per post: {engagement.get('avg_engagement_per_post', 0):.0f}."
        )
        
        # Topics summary
        if topics.get('top_keywords'):
            top_words = [k[0] for k in topics['top_keywords'][:5]]
            summary_parts.append(f"Key topics: {', '.join(top_words)}.")
        
        # Recommendations summary
        recs = analysis.get('recommendations', [])
        high_priority = [r for r in recs if r.get('priority') == 'high']
        if high_priority:
            summary_parts.append(
                f"{len(high_priority)} high-priority recommendation(s) require attention."
            )
        
        return " ".join(summary_parts)
    
    def generate_report(
        self,
        analysis: Dict,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a formatted analysis report.
        
        Args:
            analysis: Analysis results from analyze_all()
            output_path: Path to save the report (optional)
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        report.append("AI ANALYSIS REPORT - Facebook Data Insights")
        report.append("=" * 70)
        report.append("")
        
        # AI Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 50)
        report.append(analysis.get('ai_summary', 'No summary available'))
        report.append("")
        
        # Metadata
        meta = analysis.get('metadata', {})
        report.append("ANALYSIS METADATA")
        report.append("-" * 50)
        report.append(f"  Timestamp: {meta.get('analysis_timestamp', 'N/A')}")
        report.append(f"  Posts analyzed: {meta.get('total_posts', 0)}")
        report.append(f"  Comments analyzed: {meta.get('total_comments', 0)}")
        report.append(f"  Pages covered: {meta.get('pages_analyzed', 0)}")
        report.append("")
        
        # Sentiment Analysis
        sentiment = analysis.get('sentiment_analysis', {})
        report.append("SENTIMENT ANALYSIS")
        report.append("-" * 50)
        report.append(f"  Overall: {sentiment.get('overall_sentiment', 'N/A')}")
        post_sent = sentiment.get('post_sentiment', {})
        report.append(
            f"  Posts: {post_sent.get('positive', 0)}% positive, "
            f"{post_sent.get('negative', 0)}% negative, "
            f"{post_sent.get('neutral', 0)}% neutral"
        )
        report.append(f"  Trend: {sentiment.get('sentiment_trend', 'N/A')}")
        report.append("")
        
        # Engagement
        engagement = analysis.get('engagement_analysis', {})
        report.append("ENGAGEMENT METRICS")
        report.append("-" * 50)
        report.append(f"  Total engagement: {engagement.get('total_engagement', 0):,}")
        report.append(
            f"  Avg per post: {engagement.get('avg_engagement_per_post', 0):.1f}"
        )
        likes = engagement.get('likes', {})
        report.append(f"  Total likes: {likes.get('total', 0):,}")
        shares = engagement.get('shares', {})
        report.append(f"  Total shares: {shares.get('total', 0):,}")
        viral = engagement.get('viral_potential', {})
        report.append(f"  Viral potential: {viral.get('classification', 'N/A')}")
        report.append("")
        
        # Topics
        topics = analysis.get('topic_analysis', {})
        report.append("TOPIC ANALYSIS")
        report.append("-" * 50)
        if topics.get('top_keywords'):
            keywords = [f"{k[0]} ({k[1]:.3f})" for k in topics['top_keywords'][:10]]
            report.append(f"  Top keywords: {', '.join(keywords)}")
        if topics.get('dominant_themes'):
            report.append(f"  Themes: {', '.join(topics['dominant_themes'])}")
        report.append("")
        
        # Recommendations
        recs = analysis.get('recommendations', [])
        report.append("AI RECOMMENDATIONS")
        report.append("-" * 50)
        for i, rec in enumerate(recs, 1):
            priority = rec.get('priority', 'medium').upper()
            report.append(f"  {i}. [{priority}] {rec.get('recommendation', '')}")
            report.append(f"     Action: {rec.get('action', '')}")
        report.append("")
        
        report.append("=" * 70)
        report.append("End of Report")
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        # Save if path provided
        if output_path:
            Path(output_path).write_text(report_text, encoding='utf-8')
            logger.info(f"Report saved to: {output_path}")
        
        return report_text
    
    def export_analysis(
        self,
        analysis: Dict,
        output_path: str,
        format: str = 'json'
    ) -> None:
        """
        Export analysis results to file.
        
        Args:
            analysis: Analysis results
            output_path: Output file path
            format: 'json' or 'txt'
        """
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        else:
            report = self.generate_report(analysis)
            Path(output_path).write_text(report, encoding='utf-8')
        
        logger.info(f"Analysis exported to: {output_path}")
