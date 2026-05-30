"""
prepare_dataset.py
==================
Цуглуулсан Facebook группын бодит өгөгдлийг sentiment model сургалтад
бэлтгэх скрипт.

Workflow:
  1. PostgreSQL-ээс FacebookPost + PostComment өгөгдлүүдийг татах
  2. Монгол хэлний текстийг цэвэрлэх (URL, тусгай тэмдэгт, давхар зай)
  3. Гараар шошголсон (manually labeled) dataset-тэй нэгтгэх
  4. Train / Validation / Test split хийх
  5. HuggingFace Dataset форматад хадгалах

Ашиглах:
  python prepare_dataset.py --db-url postgresql://... --output data/processed/
"""

import os
import re
import json
import random
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    logger.warning("SQLAlchemy not installed. DB extraction disabled.")

from config import TRAINING_CONFIG, MONGOLIAN_CONFIG


# ─── Mongolian Text Preprocessing ─────────────────────────────────────────────

class MongolianTextPreprocessor:
    """Монгол хэлний текстийг NLP задачад бэлтгэх."""

    def __init__(self):
        self.patterns = [re.compile(p) for p in MONGOLIAN_CONFIG["remove_patterns"]]
        self.min_len = MONGOLIAN_CONFIG["min_text_length"]
        self._stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        path = MONGOLIAN_CONFIG.get("stopwords_file", "")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return {line.strip().lower() for line in f if line.strip()}
        # Default Mongolian stopwords
        return {
            "бол", "нь", "энэ", "тэр", "бас", "ч", "юм", "байна",
            "гэж", "дээр", "доор", "ба", "буюу", "учир", "тул",
            "мөн", "харин", "гэвч", "гэсэн", "байсан", "болсон",
            "хийсэн", "гэдэг", "тухай", "зэрэг", "ийм", "тийм",
        }

    def clean(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        cleaned = text.strip()
        for pattern in self.patterns:
            cleaned = pattern.sub(" ", cleaned)
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if len(cleaned) >= self.min_len else ""

    def tokenize(self, text: str) -> List[str]:
        tokens = text.lower().split()
        return [
            t for t in tokens
            if (MONGOLIAN_CONFIG["min_token_length"] <= len(t) <= MONGOLIAN_CONFIG["max_token_length"])
            and t not in self._stopwords
        ]


# ─── Database Extraction ──────────────────────────────────────────────────────

def extract_from_database(db_url: str) -> List[Dict]:
    """PostgreSQL-ээс нийтлэл болон сэтгэгдэл татах."""
    if not HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy шаардлагатай")

    engine = create_engine(db_url)
    records = []

    with engine.connect() as conn:
        # Posts
        posts = conn.execute(text("""
            SELECT post_id, page_name, content, likes, shares, comment_count, scraped_at
            FROM facebook_posts
            WHERE content IS NOT NULL AND length(content) > 10
            ORDER BY scraped_at DESC
        """))
        for row in posts:
            records.append({
                "id": f"post_{row.post_id}",
                "source": row.page_name,
                "text": row.content,
                "likes": row.likes or 0,
                "shares": row.shares or 0,
                "comments": row.comment_count or 0,
                "type": "post",
                "scraped_at": str(row.scraped_at),
            })

        # Comments
        comments = conn.execute(text("""
            SELECT pc.comment_id, fp.page_name, pc.content, pc.likes
            FROM post_comments pc
            JOIN facebook_posts fp ON fp.id = pc.post_id
            WHERE pc.content IS NOT NULL AND length(pc.content) > 5
        """))
        for row in comments:
            records.append({
                "id": f"comment_{row.comment_id}",
                "source": row.page_name,
                "text": row.content,
                "likes": row.likes or 0,
                "shares": 0,
                "comments": 0,
                "type": "comment",
                "scraped_at": "",
            })

    logger.info(f"Нийт {len(records)} бичлэг PostgreSQL-ээс татав")
    return records


# ─── Manual Label Integration ─────────────────────────────────────────────────

def load_manual_labels(labels_file: str) -> Dict[str, int]:
    """
    Гараар шошголсон CSV файлыг унших.
    Формат: id,label  (label: 0=negative, 1=neutral, 2=positive)
    """
    labels = {}
    if not os.path.exists(labels_file):
        logger.warning(f"Шошгын файл олдсонгүй: {labels_file}")
        return labels

    with open(labels_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2 and parts[1].isdigit():
                labels[parts[0]] = int(parts[1])

    logger.info(f"Гараар шошголсон {len(labels)} бичлэг уншлаа")
    return labels


# ─── Heuristic Labeling ───────────────────────────────────────────────────────

# Mongolian sentiment keyword dictionaries built from domain analysis
POSITIVE_KEYWORDS = {
    "сайн", "гоё", "гайхалтай", "баярлалаа", "амжилт", "чадна", "маш",
    "зөв", "хөгжилтэй", "дэмжинэ", "их", "хүчтэй", "тааламжтай",
    "баяртай", "мэргэжлийн", "үнэхээр", "шилдэг", "хэрэгтэй",
    "чанартай", "онцгой", "хөөрхөн", "супер", "ура", "class", "best",
    "найдвартай", "тохиромжтой", "бахархалтай", "бүтээлч", "ажилсаг",
}

NEGATIVE_KEYWORDS = {
    "муу", "болохгүй", "алдаа", "хүнд", "аймар", "аймшигтай", "харамсалтай",
    "буруу", "дутуу", "хэцүү", "ядаргаатай", "залхуу", "тааруу",
    "уучлаарай", "сул", "доголдол", "гомдол", "хамаагүй", "чадахгүй",
    "ажиллахгүй", "хаагдсан", "гутранги", "ашиггүй", "хортой",
    "асуудал", "саад", "халамжгүй", "хариуцлагагүй", "нүдэнд",
}

def heuristic_label(text: str) -> int:
    """Keyword-based heuristic labeling for unlabeled data."""
    words = set(text.lower().split())
    pos_count = len(words & POSITIVE_KEYWORDS)
    neg_count = len(words & NEGATIVE_KEYWORDS)

    if pos_count > neg_count and pos_count >= 1:
        return 2  # positive
    elif neg_count > pos_count and neg_count >= 1:
        return 0  # negative
    return 1  # neutral


# ─── Dataset Split & Save ─────────────────────────────────────────────────────

def split_dataset(
    data: List[Dict], seed: int = 42
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Train/Val/Test split."""
    random.seed(seed)
    random.shuffle(data)
    n = len(data)
    train_end = int(n * TRAINING_CONFIG["train_split"])
    val_end = train_end + int(n * TRAINING_CONFIG["val_split"])
    return data[:train_end], data[train_end:val_end], data[val_end:]


def save_split(data: List[Dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"  → {len(data)} бичлэг хадгалав: {path}")


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sentiment dataset бэлтгэх")
    parser.add_argument("--db-url", type=str, default=None, help="PostgreSQL connection string")
    parser.add_argument("--raw-json", type=str, default=None, help="Түүхий өгөгдлийн JSON файл")
    parser.add_argument("--labels", type=str, default="data/manual_labels.csv", help="Гараар шошголсон файл")
    parser.add_argument("--output", type=str, default=TRAINING_CONFIG["processed_data_dir"])
    args = parser.parse_args()

    preprocessor = MongolianTextPreprocessor()
    records = []

    # Step 1: Extract data
    if args.db_url:
        records = extract_from_database(args.db_url)
    elif args.raw_json and os.path.exists(args.raw_json):
        with open(args.raw_json, "r", encoding="utf-8") as f:
            records = json.load(f)
        logger.info(f"JSON файлаас {len(records)} бичлэг уншлаа")
    else:
        logger.error("--db-url эсвэл --raw-json заах шаардлагатай")
        return

    # Step 2: Clean text
    cleaned = []
    for rec in records:
        clean_text = preprocessor.clean(rec.get("text", ""))
        if clean_text:
            rec["text"] = clean_text
            rec["tokens"] = preprocessor.tokenize(clean_text)
            rec["token_count"] = len(rec["tokens"])
            cleaned.append(rec)
    logger.info(f"Цэвэрлэсний дараа: {len(cleaned)} / {len(records)} бичлэг")

    # Step 3: Apply labels
    manual_labels = load_manual_labels(args.labels)
    labeled_count = 0
    heuristic_count = 0

    for rec in cleaned:
        rid = rec.get("id", "")
        if rid in manual_labels:
            rec["label"] = manual_labels[rid]
            rec["label_source"] = "manual"
            labeled_count += 1
        else:
            rec["label"] = heuristic_label(rec["text"])
            rec["label_source"] = "heuristic"
            heuristic_count += 1

    logger.info(f"Шошго: гараар={labeled_count}, автомат={heuristic_count}")

    # Step 4: Split
    train, val, test = split_dataset(cleaned)

    # Step 5: Save
    save_split(train, os.path.join(args.output, "train.jsonl"))
    save_split(val, os.path.join(args.output, "val.jsonl"))
    save_split(test, os.path.join(args.output, "test.jsonl"))

    # Summary stats
    label_names = TRAINING_CONFIG["label_map"]
    for split_name, split_data in [("Train", train), ("Val", val), ("Test", test)]:
        dist = {}
        for d in split_data:
            lbl = label_names.get(d["label"], "unknown")
            dist[lbl] = dist.get(lbl, 0) + 1
        logger.info(f"{split_name} тархалт: {dist}")

    logger.info("Dataset бэлтгэл дууслаа ✓")


if __name__ == "__main__":
    main()
