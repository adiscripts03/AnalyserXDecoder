import sys
from pathlib import Path

# Add project root and src to sys.path
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
for p in [str(ROOT_DIR), str(SRC_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Execute the primary Streamlit application
from rag_app.streamlit_app import *
