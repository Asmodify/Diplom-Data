import csv
import random
from datetime import datetime, timedelta

def generate_mock_data():
    output_dir = 'mock_data'
    
    # 1. Generate facebook_posts
    pages = ["TechNews Mongolia", "Мэдээллийн Технологи", "Монголын хөгжүүлэгчид", "AI & Data Science MN"]
    contents = [
        "Шинэ хиймэл оюун ухааны загвар танилцуулагдлаа.",
        "Python 3.12 хувилбар гарлаа. Олон шинэ боломжууд нэмэгдсэн байна.",
        "Өгөгдлийн сангийн аюулгүй байдлын талаарх чухал зөвлөгөө.",
        "React 19 хувилбарыг туршиж үзсэн хүн байна уу?",
        "Шинэ iPhone 16-ийн талаарх цуурхал ба баримтууд.",
        "Cybersecurity-д хэрэгтэй шинэ tool-ууд.",
        "Javascript хөгжүүлэгчдэд зориулсан 5 зөвлөгөө.",
        "Машин сургалтын үндэс сургалт эхэллээ.",
        "Cloud computing-ийн ирээдүй.",
        "Tech event удахгүй болно."
    ]
    
    start_date = datetime(2026, 5, 1)
    
    with open(f'{output_dir}/facebook_posts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'page_name', 'post_id', 'post_url', 'content', 'timestamp', 'likes', 'shares', 'comment_count', 'scraped_at'])
        for i in range(1, 501):
            page = random.choice(pages)
            post_id = f"POST_{i:04d}"
            url = f"https://facebook.com/{page.replace(' ', '').lower()}/posts/{i}"
            content = random.choice(contents) + f" #{i}"
            timestamp = start_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            likes = random.randint(10, 1000)
            shares = random.randint(0, 200)
            comments = random.randint(0, 100)
            scraped_at = timestamp + timedelta(hours=2)
            
            writer.writerow([i, page, post_id, url, content, timestamp.strftime("%Y-%m-%d %H:%M:%S"), likes, shares, comments, scraped_at.strftime("%Y-%m-%d %H:%M:%S")])

    # 2. Generate post_comments
    authors = ["Bat-Erdene", "Nomin", "Gantulga", "Sarnai", "Tuguldur", "Anu", "Odbayar", "Khuslen", "Tengis", "Maral"]
    comment_texts = [
        "Маш сонирхолтой мэдээлэл байна.",
        "Энэ талаар дэлгэрэнгүй хаанаас уншиж болох вэ?",
        "Хэрэгтэй зөвлөгөө байна баярлалаа.",
        "Үүнтэй санал нийлэхгүй байна.",
        "Үнэхээр гоё санагдсан шүү.",
        "Асуух зүйл байна, dm шалгаарай.",
        "Дараагийн пост хэзээ орох вэ?",
        "Гайхалтай!",
        "Сайн тайлбарлажээ.",
        "Хэрэгжүүлж үзнэ ээ."
    ]
    
    with open(f'{output_dir}/post_comments.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'post_id', 'comment_id', 'author_name', 'author_url', 'content', 'timestamp', 'likes', 'reply_to_id', 'scraped_at'])
        for i in range(1, 501):
            post_id = random.randint(1, 500)
            comment_id = f"C_{i:05d}"
            author = random.choice(authors)
            author_url = f"https://facebook.com/{author.lower()}"
            content = random.choice(comment_texts)
            timestamp = start_date + timedelta(days=random.randint(5, 25), hours=random.randint(0, 23))
            likes = random.randint(0, 50)
            reply_to = "" if random.random() > 0.2 or i == 1 else random.randint(1, i-1)
            scraped_at = timestamp + timedelta(hours=1)
            
            writer.writerow([i, post_id, comment_id, author, author_url, content, timestamp.strftime("%Y-%m-%d %H:%M:%S"), likes, reply_to, scraped_at.strftime("%Y-%m-%d %H:%M:%S")])

    # 3. Generate post_images
    with open(f'{output_dir}/post_images.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'post_id', 'image_url', 'local_path', 'downloaded_at'])
        for i in range(1, 501):
            post_id = random.randint(1, 500)
            url = f"https://example.com/images/img_{i}.jpg"
            local = f"images/img_{i}.jpg"
            downloaded = start_date + timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
            
            writer.writerow([i, post_id, url, local, downloaded.strftime("%Y-%m-%d %H:%M:%S")])

if __name__ == "__main__":
    generate_mock_data()
    print("Successfully generated 500 rows for each mock data file.")
