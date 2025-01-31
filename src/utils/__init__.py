import sys
from pathlib import Path

def setup_python_path():
    """Add project root to Python path"""
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    return project_root
