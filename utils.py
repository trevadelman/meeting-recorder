import sys
from pathlib import Path

def setup_python_path():
    """Add parent directory to Python path to access core modules"""
    root_dir = Path(__file__).resolve().parent
    if str(root_dir) not in sys.path:
        sys.path.append(str(root_dir))
