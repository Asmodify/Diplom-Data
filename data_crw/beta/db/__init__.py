from .database import DatabaseManager
from .models import FacebookPost, PostImage, PostComment, Base
from .config import get_database_url, get_image_path

__all__ = [
    'DatabaseManager',
    'FacebookPost',
    'PostImage',
    'PostComment',
    'Base',
    'get_database_url',
    'get_image_path'
]

def init_package():
    """Initialize database package and ensure required paths exist"""
    from pathlib import Path
    
    # Get project root (parent of db folder)
    project_root = Path(__file__).parent.parent
    
    # Create required directories if they don't exist
    required_dirs = [
        project_root / 'db',
        project_root / 'images',
        project_root / 'logs',
        project_root / 'debug'
    ]
    
    for directory in required_dirs:
        directory.mkdir(exist_ok=True)
        
init_package()
