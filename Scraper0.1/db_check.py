import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

db_url = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(db_url)

print("Checking database connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection successful:", result.scalar() == 1)
        print("\nSample data from facebook_posts:")
        result = conn.execute(text("SELECT * FROM facebook_posts LIMIT 10"))
        for row in result:
            print(row)
except Exception as e:
    print("Database connection failed:", e)
