import sys
from pathlib import Path

def setup_python_path():
    """Add parent directory to Python path to access core modules"""
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.append(str(parent_dir))
