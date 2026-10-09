import sys
import os
from pathlib import Path

# Ensure 'src' is in sys.path
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import and expose the FastAPI ASGI application for Vercel / Uvicorn
from rag_app.server import app

# Re-export pipeline modules for CLI usage
from rag_app.main import (
    ingest_webpage,
    ingest_pdf_file,
    answer_query,
    build_rag_chain,
    get_llm,
    run_interactive_mode,
    parse_args,
    check_api_key,
    clear_collection,
)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        from rag_app.main import main as cli_main
        cli_main()
    else:
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development" and "PORT" not in os.environ
        print("=" * 65)
        print("🌐 AnalyserXDecoder — HTML/CSS Web UI")
        print(f"🚀 Server running at: http://0.0.0.0:{port}")
        print(f"⚙️  Mode: {'Development (reload enabled)' if is_dev else 'Production'}")
        print("=" * 65)
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
