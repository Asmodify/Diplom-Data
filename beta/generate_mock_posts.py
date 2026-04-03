"""
Generate mock Facebook post data and save it to exports.
If the database is available, it will also try to insert posts.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


def _random_text() -> str:
    starts = [
        "Breaking update:",
        "Daily highlight:",
        "Community note:",
        "New post:",
        "Quick update:",
        "Today we share:",
    ]
    topics = [
        "economy trends",
        "tech innovation",
        "sports recap",
        "education reforms",
        "public transport",
        "weather alert",
        "health tips",
        "startup news",
        "media briefing",
        "city development",
    ]
    endings = [
        "Read more in comments.",
        "Share your thoughts below.",
        "What do you think?",
        "Follow for more updates.",
        "Stay tuned for details.",
    ]
    return f"{random.choice(starts)} {random.choice(topics)}. {random.choice(endings)}"


def _make_post(i: int, base_time: datetime) -> Dict[str, Any]:
    dt = base_time - timedelta(minutes=i * random.randint(3, 25))
    comment_count = random.randint(0, 120)
    comments: List[Dict[str, Any]] = []
    for c in range(min(comment_count, 8)):
        comments.append(
            {
                "comment_id": f"mock_comment_{i}_{c}",
                "author": f"user_{random.randint(1, 5000)}",
                "author_url": "",
                "content": _random_text(),
                "timestamp": dt.isoformat(),
                "likes": random.randint(0, 250),
                "replies": [],
            }
        )

    page = random.choice(
        [
            "eaglenewssocial",
            "zarigmn",
            "gogo.mn",
            "mongoltvorgiltsag",
            "iKonNews",
            "profile.php?id=61553882396168",
        ]
    )

    return {
        "post_id": f"mock_post_{i:05d}",
        "post_url": f"https://www.facebook.com/{page}/posts/{1000000 + i}",
        "page_name": page,
        "content": _random_text(),
        "timestamp": dt.isoformat(),
        "likes": random.randint(0, 20000),
        "shares": random.randint(0, 6000),
        "comment_count": comment_count,
        "images": [],
        "comments": comments,
    }


def _save_json(posts: List[Dict[str, Any]], exports_dir: Path) -> Path:
    exports_dir.mkdir(parents=True, exist_ok=True)
    out = exports_dir / f"mock_posts_{len(posts)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    return out


def _try_insert_db(posts: List[Dict[str, Any]]) -> int:
    try:
        from db.database import DatabaseManager
        from db.models import FacebookPost

        db = DatabaseManager()
        db.init_db()
        inserted = 0
        for p in posts:
            exists = db.session.query(FacebookPost).filter_by(post_id=p["post_id"]).first()
            if exists:
                continue
            obj = FacebookPost(
                page_name=p["page_name"],
                post_id=p["post_id"],
                post_url=p["post_url"],
                content=p["content"],
                timestamp=datetime.fromisoformat(p["timestamp"]),
                likes=p["likes"],
                shares=p["shares"],
                comment_count=p["comment_count"],
            )
            db.session.add(obj)
            inserted += 1
        db.session.commit()
        return inserted
    except Exception:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock Facebook post data")
    parser.add_argument("--count", type=int, default=1000, help="Number of mock posts")
    args = parser.parse_args()

    base_time = datetime.now()
    posts = [_make_post(i, base_time) for i in range(args.count)]

    project_root = Path(__file__).parent
    out_file = _save_json(posts, project_root / "exports")
    inserted = _try_insert_db(posts)

    print(f"Generated posts: {len(posts)}")
    print(f"Saved JSON: {out_file}")
    if inserted > 0:
        print(f"Inserted into DB: {inserted}")
    else:
        print("DB insert skipped or unavailable.")


if __name__ == "__main__":
    main()
