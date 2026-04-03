import os
from pathlib import Path

def init_directories():
    dirs = [
        "images",
        "logs",
        "debug",
        "exports",
        "data/posts",
        "data/images",
        "data/comments"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("All required directories initialized.")

if __name__ == "__main__":
    init_directories()
