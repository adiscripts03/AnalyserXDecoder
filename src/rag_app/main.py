"""Package entrypoint re-exporting RAG pipeline from main module."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import main as root_main

ingest_webpage = root_main.ingest_webpage
ingest_pdf_file = root_main.ingest_pdf_file
answer_query = root_main.answer_query
build_rag_chain = root_main.build_rag_chain
get_llm = root_main.get_llm
run_interactive_mode = root_main.run_interactive_mode
main = root_main.main

if __name__ == "__main__":
    main()
