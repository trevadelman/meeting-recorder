#!/usr/bin/env python3.11
"""
Script to ensure uvicorn runs with Python 3.11
"""
import uvicorn
import sys

if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required")
        sys.exit(1)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
