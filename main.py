import sys
from pathlib import Path

# Ensure 'src' is in sys.path so 'rag_app' can be imported directly
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_app.main import *
from rag_app.main import main

if __name__ == "__main__":
    main()
