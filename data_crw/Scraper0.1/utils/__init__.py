import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(name: str, log_file: str = None, log_dir: str = "logs") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if log_file:
        log_path = Path(log_dir) / log_file
        Path(log_dir).mkdir(exist_ok=True)
        fh = RotatingFileHandler(log_path, maxBytes=2*1024*1024, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
