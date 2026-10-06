import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# Ensure 'src' is in sys.path so modules in rag_app can be resolved seamlessly
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from rag_app.document_loader import load_url, load_pdf, split_documents
from rag_app.vector_store import (
    add_documents_to_vector_store,
    clear_collection,
    get_vector_store,
    PERSIST_DIRECTORY,
)
from rag_app.retriever import (
    get_retriever,
    get_similarity_retriever,
    get_mmr_retriever,
    format_retrieved_documents,
)

# Load environment variables (.env)
load_dotenv()

DEFAULT_COLLECTION = "webpage_decoder"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]

# Grounded RAG system prompt
RAG_PROMPT_TEMPLATE = """You are WebpageDecoder, an intelligent AI research assistant that decodes webpages and documents to their core.
Answer the user's question accurately, clearly, and concisely using ONLY the provided context.
If the answer cannot be found or deduced from the context, state honestly:
"I am sorry, but the provided documents do not contain enough information to answer this question."
Do not extrapolate or hallucinate facts beyond the given context.

Context:
{context}

Question:
{question}

Answer (with citations referencing the sources above, e.g. [Source 1], [Source 2]):"""


def check_api_key() -> bool:
    """Verifies that the Google Gemini API key is configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n" + "!" * 60)
        print("⚠️  WARNING: GOOGLE_API_KEY is not set!")
        print("Please set your GOOGLE_API_KEY in the .env file or environment.")
        print("Get your API key at: https://aistudio.google.com/")
        print("!" * 60 + "\n")
        return False
    return True


def get_llm(model_name: Optional[str] = None, temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """Initializes and returns the ChatGoogleGenerativeAI model."""
    selected_model = model_name or DEFAULT_MODEL
    return ChatGoogleGenerativeAI(
        model=selected_model,
        temperature=temperature,
    )


def build_rag_chain(model_name: Optional[str] = None):
    """Builds a LangChain runnable RAG chain."""
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    llm = get_llm(model_name=model_name)
    return prompt | llm | StrOutputParser()


def ingest_webpage(
    url: str,
    collection_name: str = DEFAULT_COLLECTION,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingests, chunks, and stores content from a webpage URL into ChromaDB.

    Args:
        url: The web URL to scrape.
        collection_name: Name of the ChromaDB collection.
        chunk_size: Size of semantic text chunks in characters.
        chunk_overlap: Overlap between adjacent chunks in characters.

    Returns:
        int: Number of chunks added to the vector store.
    """
    print(f"\n🌐 Scraping content from: {url}")
    try:
        docs = load_url(url)
    except Exception as e:
        print(f"❌ Error loading URL: {e}")
        return 0

    if not docs:
        print("⚠️ No content could be extracted from the provided URL.")
        return 0

    chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"✂️  Split document into {len(chunks)} chunks.")

    print(f"💾 Generating embeddings and storing into collection '{collection_name}'...")
    add_documents_to_vector_store(chunks, collection_name=collection_name)
    print(f"✅ Successfully ingested {len(chunks)} chunks into ChromaDB at:\n   {PERSIST_DIRECTORY}\n")
    return len(chunks)


def ingest_pdf_file(
    file_path: str,
    collection_name: str = DEFAULT_COLLECTION,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingests, chunks, and stores content from a local PDF file into ChromaDB.

    Args:
        file_path: Absolute or relative path to PDF file.
        collection_name: Name of the ChromaDB collection.
        chunk_size: Size of semantic text chunks in characters.
        chunk_overlap: Overlap between adjacent chunks in characters.

    Returns:
        int: Number of chunks added to the vector store.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    print(f"\n📄 Reading PDF from: {path}")
    try:
        docs = load_pdf(str(path))
    except Exception as e:
        print(f"❌ Error loading PDF: {e}")
        return 0

    if not docs:
        print("⚠️ No content could be extracted from the PDF.")
        return 0

    chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"✂️  Split PDF into {len(chunks)} chunks.")

    print(f"💾 Generating embeddings and storing into collection '{collection_name}'...")
    add_documents_to_vector_store(chunks, collection_name=collection_name)
    print(f"✅ Successfully ingested {len(chunks)} chunks into ChromaDB at:\n   {PERSIST_DIRECTORY}\n")
    return len(chunks)


def answer_query(
    question: str,
    collection_name: str = DEFAULT_COLLECTION,
    search_type: str = "similarity",
    k: int = 4,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves relevant context and generates a grounded answer using Google Gemini.

    Args:
        question: User's query string.
        collection_name: Target Chroma collection.
        search_type: Strategy ('similarity' or 'mmr').
        k: Number of relevant chunks to retrieve.
        model_name: Gemini model name.

    Returns:
        Dict containing 'answer', 'documents', and 'context'.
    """
    retriever = get_retriever(
        collection_name=collection_name,
        search_type=search_type,
        k=k,
    )

    retrieved_docs: List[Document] = retriever.invoke(question)
    if not retrieved_docs:
        return {
            "answer": "No relevant documents found in the vector store. Please ingest a URL or PDF first.",
            "documents": [],
            "context": "",
        }

    formatted_context = format_retrieved_documents(retrieved_docs)

    # Models with automatic fallback if the primary model hits rate limits or temporary demand spikes
    candidate_models = [model_name or DEFAULT_MODEL] + [m for m in FALLBACK_MODELS if m != (model_name or DEFAULT_MODEL)]
    last_error = None
    answer = None

    for candidate in candidate_models:
        try:
            chain = build_rag_chain(model_name=candidate)
            answer = chain.invoke({
                "context": formatted_context,
                "question": question,
            })
            break
        except Exception as e:
            last_error = e
            continue

    if answer is None:
        raise RuntimeError(f"Failed to generate answer from Gemini ({last_error})")

    return {
        "answer": answer,
        "documents": retrieved_docs,
        "context": formatted_context,
    }


def launch_streamlit() -> None:
    """Launches the Streamlit user interface."""
    app_path = Path(__file__).resolve().parent / "src" / "rag_app" / "app.py"
    print(f"\n🚀 Launching Streamlit UI ({app_path})...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
    except KeyboardInterrupt:
        print("\nStreamlit server stopped.")


def run_interactive_mode(
    collection_name: str = DEFAULT_COLLECTION,
    search_type: str = "similarity",
    k: int = 4,
    model_name: Optional[str] = None,
) -> None:
    """Runs the interactive command-line interface."""
    print("=" * 65)
    print("🌐  WebpageDecoder — Wikipedia of Webpages (Interactive CLI)")
    print("=" * 65)
    print(f"• Active Collection: {collection_name}")
    print(f"• Search Strategy:   {search_type} (top {k} chunks)")
    print(f"• LLM Model:         {model_name or DEFAULT_MODEL}")
    print("=" * 65)

    while True:
        print("\nMenu:")
        print("  [1] Ingest Webpage URL")
        print("  [2] Ingest PDF File")
        print("  [3] Ask a Question (Conversational Q&A)")
        print("  [4] Clear / Reset Collection")
        print("  [5] Launch Streamlit Web UI")
        print("  [6] Exit")

        try:
            choice = input("\nEnter choice [1-6]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break

        if choice == "1":
            url = input("Enter Webpage URL: ").strip()
            if not url:
                print("❌ URL cannot be empty.")
                continue
            try:
                ingest_webpage(url, collection_name=collection_name)
            except Exception as e:
                print(f"❌ Failed to ingest URL: {e}")

        elif choice == "2":
            pdf_path = input("Enter PDF file path: ").strip()
            if not pdf_path:
                print("❌ Path cannot be empty.")
                continue
            try:
                ingest_pdf_file(pdf_path, collection_name=collection_name)
            except Exception as e:
                print(f"❌ Failed to ingest PDF: {e}")

        elif choice == "3":
            print("\n--- Conversational Q&A (Press Enter with empty input to return to menu) ---")
            while True:
                try:
                    question = input("\n💬 Your question: ").strip()
                except (KeyboardInterrupt, EOFError):
                    break
                if not question:
                    break

                print("\n🔍 Retrieving context & generating answer with Gemini...\n")
                try:
                    result = answer_query(
                        question=question,
                        collection_name=collection_name,
                        search_type=search_type,
                        k=k,
                        model_name=model_name,
                    )
                    print("-" * 60)
                    print("💡 Answer:\n")
                    print(result["answer"])
                    print("-" * 60)
                    print(f"📚 Sources Cited ({len(result['documents'])} chunks retrieved):")
                    for idx, doc in enumerate(result["documents"], start=1):
                        src = doc.metadata.get("source", "Unknown Source")
                        title = doc.metadata.get("title", "")
                        label = f"{src} | {title}" if title else src
                        print(f"  [{idx}] {label}")
                    print("-" * 60)
                except Exception as e:
                    print(f"❌ Query error: {e}")

        elif choice == "4":
            confirm = input(f"Are you sure you want to clear collection '{collection_name}'? (y/N): ").strip().lower()
            if confirm == "y":
                try:
                    clear_collection(collection_name)
                    print(f"🗑️ Collection '{collection_name}' cleared successfully!")
                except Exception as e:
                    print(f"❌ Error clearing collection: {e}")

        elif choice == "5":
            launch_streamlit()

        elif choice == "6":
            print("Goodbye! 👋")
            break

        else:
            print("Invalid choice. Please select 1 through 6.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebpageDecoder — RAG-powered Q&A over webpages and documents with Google Gemini."
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL of the webpage to ingest into the vector store.",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to a PDF document to ingest into the vector store.",
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="A question to query against the ingested knowledge base.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION,
        help=f"ChromaDB collection name (default: '{DEFAULT_COLLECTION}').",
    )
    parser.add_argument(
        "--search-type",
        type=str,
        choices=["similarity", "mmr"],
        default="similarity",
        help="Retrieval strategy: 'similarity' (default) or 'mmr' (Maximal Marginal Relevance).",
    )
    parser.add_argument(
        "-k",
        type=int,
        default=4,
        help="Number of document chunks to retrieve (default: 4).",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the vector store collection before processing.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Gemini chat model to use (default: gemini-3.5-flash).",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Streamlit web application.",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive terminal mode.",
    )
    return parser.parse_args()


def main() -> None:
    """Main application entry point."""
    check_api_key()
    args = parse_args()

    # Launch Streamlit UI
    if args.ui:
        launch_streamlit()
        return

    # Clear collection if requested
    if args.clear:
        print(f"🗑️ Clearing collection '{args.collection}'...")
        try:
            clear_collection(args.collection)
            print("Collection cleared.")
        except Exception as e:
            print(f"Failed to clear collection: {e}")

    # Ingest URL if provided
    if args.url:
        ingest_webpage(args.url, collection_name=args.collection)

    # Ingest PDF if provided
    if args.pdf:
        ingest_pdf_file(args.pdf, collection_name=args.collection)

    # If query is passed, run one-shot query
    if args.query:
        print(f"\n❓ Question: {args.query}\n")
        try:
            result = answer_query(
                question=args.query,
                collection_name=args.collection,
                search_type=args.search_type,
                k=args.k,
                model_name=args.model,
            )
            print("💡 Answer:\n")
            print(result["answer"])
            print("\n📚 Sources:")
            for idx, doc in enumerate(result["documents"], start=1):
                src = doc.metadata.get("source", "Unknown Source")
                print(f"  [{idx}] {src}")
        except Exception as e:
            print(f"❌ Error querying knowledge base: {e}")
        return

    # If neither query nor ingest URL/PDF was provided, or if interactive flag was given
    if args.interactive or (not args.url and not args.pdf and not args.clear):
        run_interactive_mode(
            collection_name=args.collection,
            search_type=args.search_type,
            k=args.k,
            model_name=args.model,
        )


if __name__ == "__main__":
    main()
