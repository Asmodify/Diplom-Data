import logging
from db.database import DatabaseManager

def main():
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager()
    db.create_tables()
    print("Database initialized.")

if __name__ == "__main__":
    main()
