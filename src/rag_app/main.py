import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI

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

# Model provider configurations
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
DEFAULT_MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-7b")

GEMINI_FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]
MISTRAL_FALLBACK_MODELS = ["mistral-small-latest"]

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


def check_api_key(provider: str = DEFAULT_PROVIDER) -> bool:
    """Verifies that the appropriate API key is configured for the selected provider."""
    provider_clean = provider.lower()
    if provider_clean == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("\n" + "!" * 60)
            print("⚠️  WARNING: MISTRAL_API_KEY is not set!")
            print("Please set your MISTRAL_API_KEY in the .env file or environment.")
            print("Get your API key at: https://console.mistral.ai/")
            print("!" * 60 + "\n")
            return False
        return True
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("\n" + "!" * 60)
            print("⚠️  WARNING: GOOGLE_API_KEY is not set!")
            print("Please set your GOOGLE_API_KEY in the .env file or environment.")
            print("Get your API key at: https://aistudio.google.com/")
            print("!" * 60 + "\n")
            return False
        return True


def get_llm(
    provider: str = DEFAULT_PROVIDER,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
):
    """Initializes and returns the Chat model for either Gemini or Mistral."""
    provider_clean = provider.lower()
    if provider_clean == "mistral":
        selected_model = model_name or DEFAULT_MISTRAL_MODEL
        return ChatMistralAI(
            model=selected_model,
            temperature=temperature,
        )
    else:
        selected_model = model_name or DEFAULT_GEMINI_MODEL
        return ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=temperature,
        )


def build_rag_chain(
    provider: str = DEFAULT_PROVIDER,
    model_name: Optional[str] = None,
):
    """Builds a LangChain runnable RAG chain using the chosen provider."""
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
    llm = get_llm(provider=provider, model_name=model_name)
    return prompt | llm | StrOutputParser()


def ingest_webpage(
    url: str,
    collection_name: str = DEFAULT_COLLECTION,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> int:
    """Ingests, chunks, and stores content from a webpage URL into ChromaDB."""
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
    """Ingests, chunks, and stores content from a local PDF file into ChromaDB."""
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
    provider: str = DEFAULT_PROVIDER,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves relevant context and generates a grounded answer using the selected LLM provider."""
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
            "provider": provider,
        }

    formatted_context = format_retrieved_documents(retrieved_docs)

    provider_clean = provider.lower()
    if provider_clean == "mistral":
        default_model = DEFAULT_MISTRAL_MODEL
        fallbacks = MISTRAL_FALLBACK_MODELS
    else:
        default_model = DEFAULT_GEMINI_MODEL
        fallbacks = GEMINI_FALLBACK_MODELS

    primary = model_name or default_model
    candidate_models = [primary] + [m for m in fallbacks if m != primary]
    last_error = None
    answer = None

    for candidate in candidate_models:
        try:
            chain = build_rag_chain(provider=provider_clean, model_name=candidate)
            answer = chain.invoke({
                "context": formatted_context,
                "question": question,
            })
            break
        except Exception as e:
            last_error = e
            continue

    if answer is None:
        raise RuntimeError(f"Failed to generate answer from {provider.capitalize()} ({last_error})")

    return {
        "answer": answer,
        "documents": retrieved_docs,
        "context": formatted_context,
        "provider": provider_clean,
    }


def launch_web_ui(port: int = 8000) -> None:
    """Launches the modern HTML/CSS web interface."""
    import uvicorn
    print(f"\n🚀 Launching HTML/CSS Web UI at: http://localhost:{port}")
    try:
        uvicorn.run("rag_app.server:app", host="0.0.0.0", port=port, reload=True)
    except KeyboardInterrupt:
        print("\nWeb server stopped.")


def run_interactive_mode(
    collection_name: str = DEFAULT_COLLECTION,
    search_type: str = "similarity",
    k: int = 4,
    provider: str = DEFAULT_PROVIDER,
    model_name: Optional[str] = None,
) -> None:
    """Runs the interactive command-line interface."""
    current_provider = provider.lower()
    current_model = model_name

    while True:
        display_model = current_model or (DEFAULT_MISTRAL_MODEL if current_provider == "mistral" else DEFAULT_GEMINI_MODEL)
        print("=" * 65)
        print("🌐  WebpageDecoder — Wikipedia of Webpages (Interactive CLI)")
        print("=" * 65)
        print(f"• Active Collection: {collection_name}")
        print(f"• Search Strategy:   {search_type} (top {k} chunks)")
        print(f"• LLM Provider:      {current_provider.upper()} ({display_model})")
        print("=" * 65)

        print("\nMenu:")
        print("  [1] Ingest Webpage URL")
        print("  [2] Ingest PDF File")
        print("  [3] Ask a Question (Conversational Q&A)")
        print("  [4] Switch LLM Provider (Gemini / Mistral)")
        print("  [5] Clear / Reset Collection")
        print("  [6] Launch Streamlit Web UI")
        print("  [7] Exit")

        try:
            choice = input("\nEnter choice [1-7]: ").strip()
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
            print(f"\n--- Conversational Q&A with {current_provider.upper()} (Press Enter with empty input to return) ---")
            while True:
                try:
                    question = input("\n💬 Your question: ").strip()
                except (KeyboardInterrupt, EOFError):
                    break
                if not question:
                    break

                print(f"\n🔍 Retrieving context & generating answer with {current_provider.capitalize()}...\n")
                try:
                    result = answer_query(
                        question=question,
                        collection_name=collection_name,
                        search_type=search_type,
                        k=k,
                        provider=current_provider,
                        model_name=current_model,
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
            print(f"\nCurrent provider: {current_provider.upper()}")
            print("  [1] Gemini (models: gemini-3.5-flash, gemini-3.8-flash)")
            print("  [2] Mistral (models: open-mistral-7b, mistral-small-latest)")
            p_choice = input("Select provider [1-2]: ").strip()
            if p_choice == "1":
                current_provider = "gemini"
                current_model = None
                print("Switched to Google Gemini.")
            elif p_choice == "2":
                current_provider = "mistral"
                current_model = None
                print("Switched to Mistral AI.")
            else:
                print("Invalid choice, keeping current provider.")

        elif choice == "5":
            confirm = input(f"Are you sure you want to clear collection '{collection_name}'? (y/N): ").strip().lower()
            if confirm == "y":
                try:
                    clear_collection(collection_name)
                    print(f"🗑️ Collection '{collection_name}' cleared successfully!")
                except Exception as e:
                    print(f"❌ Error clearing collection: {e}")

        elif choice == "6":
            launch_web_ui()

        elif choice == "7":
            print("Goodbye! 👋")
            break

        else:
            print("Invalid choice. Please select 1 through 7.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WebpageDecoder — RAG-powered Q&A over webpages and documents with Google Gemini & Mistral AI."
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
        "--provider",
        type=str,
        choices=["gemini", "mistral"],
        default=DEFAULT_PROVIDER,
        help="LLM Provider: 'gemini' (default) or 'mistral'.",
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
        help="Specific model name (defaults to gemini-3.5-flash for Gemini or open-mistral-7b for Mistral).",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the HTML/CSS web application.",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive terminal mode.",
    )
    return parser.parse_args()


def main() -> None:
    """Main application entry point."""
    args = parse_args()
    check_api_key(args.provider)

    if args.ui:
        launch_web_ui()
        return

    if args.clear:
        print(f"🗑️ Clearing collection '{args.collection}'...")
        try:
            clear_collection(args.collection)
            print("Collection cleared.")
        except Exception as e:
            print(f"Failed to clear collection: {e}")

    if args.url:
        ingest_webpage(args.url, collection_name=args.collection)

    if args.pdf:
        ingest_pdf_file(args.pdf, collection_name=args.collection)

    if args.query:
        print(f"\n❓ Question: {args.query}")
        print(f"🤖 Provider: {args.provider.capitalize()}\n")
        try:
            result = answer_query(
                question=args.query,
                collection_name=args.collection,
                search_type=args.search_type,
                k=args.k,
                provider=args.provider,
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

    if args.interactive or (not args.url and not args.pdf and not args.clear):
        run_interactive_mode(
            collection_name=args.collection,
            search_type=args.search_type,
            k=args.k,
            provider=args.provider,
            model_name=args.model,
        )


if __name__ == "__main__":
    main()
