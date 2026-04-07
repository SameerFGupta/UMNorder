"""
Simple script to run the application locally
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting UMN Order server...")
    print("=" * 60)
    print("\n🌐 Access the website at:")
    print("   http://localhost:8000")
    print("   or")
    print("   http://127.0.0.1:8000")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
