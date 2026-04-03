"""Test script for ML analyzer and integrations"""
import sys
sys.path.insert(0, '.')

from ml.analyzer import DataAnalyzer
print('Testing ML Analyzer...')

# Initialize
analyzer = DataAnalyzer()

# Test with sample data
posts = [
    {'post_id': '1', 'content': 'This is amazing! Great news for everyone!', 'likes': 1000, 'shares': 200, 'comment_count': 50},
    {'post_id': '2', 'content': 'Terrible disaster strikes the city today', 'likes': 50, 'shares': 10, 'comment_count': 100},
    {'post_id': '3', 'content': 'Weather forecast shows sunny day tomorrow', 'likes': 200, 'shares': 30, 'comment_count': 20}
]

# Test sentiment analysis
print('\n--- Sentiment Analysis ---')
sentiments = analyzer.analyze_sentiment(posts)
for post_id, result in sentiments.items():
    print(f"Post {post_id}: {result['sentiment']} (polarity: {result['polarity']})")

# Test topic classification
print('\n--- Topic Classification ---')
topics = analyzer.classify_topics(posts)
for post_id, result in topics.items():
    print(f"Post {post_id}: {result['topic_name']} (prob: {result['topic_probability']})")

# Test engagement prediction
print('\n--- Engagement Prediction ---')
engagement = analyzer.predict_engagement(posts)
for post_id, result in engagement.items():
    print(f"Post {post_id}: score={result['engagement_score']}, level={result['engagement_level']}")

# Test full analysis
print('\n--- Full Analysis ---')
full = analyzer.analyze_all(posts)
print(f"Analyzed {len(full)} posts")

# Get summary stats
print('\n--- Summary Stats ---')
stats = analyzer.get_summary_stats(posts)
print(f"Sentiment distribution: {stats['sentiment_distribution']}")
print(f"Engagement distribution: {stats['engagement_distribution']}")

print('\n✓ ML Analyzer working!')
