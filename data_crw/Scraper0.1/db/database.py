import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from .config import USE_SQLITE, SQLITE_DB_PATH, DB_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        if USE_SQLITE:
            db_url = f"sqlite:///{SQLITE_DB_PATH}"
        else:
            db_url = (
                f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@"
                f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            )
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created.")
