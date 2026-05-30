# Sentiment Model Training Configuration
# Used for fine-tuning multilingual transformer on Mongolian Facebook data

TRAINING_CONFIG = {
    "base_model": "bert-base-multilingual-cased",
    "task": "sequence_classification",
    "num_labels": 3,  # positive, negative, neutral
    "label_map": {
        0: "negative",
        1: "neutral",
        2: "positive"
    },

    # Training hyperparameters (tuned via grid search)
    "learning_rate": 2e-5,
    "epochs": 3,
    "batch_size": 16,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "max_seq_length": 256,
    "gradient_accumulation_steps": 2,

    # Data split
    "train_split": 0.8,
    "val_split": 0.1,
    "test_split": 0.1,
    "random_seed": 42,

    # Data sources (Facebook groups scraped)
    "data_sources": [
        "https://www.facebook.com/groups/369785350059670",
        "https://www.facebook.com/groups/995968413758817",
        "https://www.facebook.com/spacehub.mn",
    ],

    # Paths
    "raw_data_dir": "data/raw/",
    "processed_data_dir": "data/processed/",
    "model_output_dir": "models/mongolian_sentiment_v1/",
    "logs_dir": "logs/training/",
}

# Mongolian-specific preprocessing settings
MONGOLIAN_CONFIG = {
    "remove_patterns": [
        r"https?://\S+",           # URLs
        r"@\w+",                   # Mentions
        r"#\w+",                   # Hashtags (kept separately for topic analysis)
        r"[^\w\s\u0400-\u04FF]",   # Non-Cyrillic special chars
    ],
    "min_token_length": 2,
    "max_token_length": 50,
    "min_text_length": 5,          # Minimum chars to be considered valid
    "stopwords_file": "data/mongolian_stopwords.txt",
}
