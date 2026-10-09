import os
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_chroma import Chroma
from rag_app.embeddings import ResilientGoogleEmbeddings

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PERSIST_DIRECTORY = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(PROJECT_ROOT / "vectorstore" / "chroma_db")))
PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_embedding_model() -> ResilientGoogleEmbeddings:
    """Returns resilient Google embedding function with rate-limit retries."""
    return ResilientGoogleEmbeddings()


def get_vector_store(collection_name: str = "webpage_decoder") -> Chroma:
    """Retrieves or creates a ChromaDB vector store collection."""
    embeddings = get_embedding_model()
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(PERSIST_DIRECTORY),
    )


def add_documents_to_vector_store(
    documents: List[Document],
    collection_name: str = "webpage_decoder",
    batch_size: int = 25,
) -> Chroma:
    """Adds documents into ChromaDB in resilient batches with sanitized metadata."""
    if not documents:
        return get_vector_store(collection_name=collection_name)

    # Sanitize documents and metadata for ChromaDB compatibility
    clean_docs: List[Document] = []
    for doc in documents:
        content = (doc.page_content or "").replace("\x00", " ").strip()
        if not content:
            continue
        
        # Ensure metadata has valid scalar types
        clean_metadata = {}
        if doc.metadata:
            for k, v in doc.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                elif v is not None:
                    clean_metadata[k] = str(v)

        clean_docs.append(Document(page_content=content, metadata=clean_metadata))

    if not clean_docs:
        return get_vector_store(collection_name=collection_name)

    vector_store = get_vector_store(collection_name=collection_name)

    # Add in safe sub-batches to prevent memory pressure and large transactions
    total = len(clean_docs)
    for i in range(0, total, batch_size):
        batch = clean_docs[i : i + batch_size]
        vector_store.add_documents(batch)

    return vector_store


def similarity_search(
    query: str,
    k: int = 4,
    collection_name: str = "webpage_decoder",
) -> List[Document]:
    """Performs cosine similarity search."""
    vector_store = get_vector_store(collection_name=collection_name)
    return vector_store.similarity_search(query, k=k)


def similarity_search_with_score(
    query: str,
    k: int = 4,
    collection_name: str = "webpage_decoder",
) -> List[Tuple[Document, float]]:
    """Performs similarity search returning cosine distances."""
    vector_store = get_vector_store(collection_name=collection_name)
    return vector_store.similarity_search_with_score(query, k=k)


def clear_collection(collection_name: str = "webpage_decoder") -> None:
    """Removes the entire collection from the vector store."""
    vector_store = get_vector_store(collection_name=collection_name)
    vector_store.delete_collection()


if __name__ == "__main__":
    from rag_app.document_loader import load_url, split_documents

    sample_url = "https://en.wikipedia.org/wiki/Information_retrieval"
    print(f"1. Loading and chunking: {sample_url}")
    
    docs = load_url(sample_url)
    chunks = split_documents(docs, chunk_size=800, chunk_overlap=150)
    print(f"Total chunks created: {len(chunks)}")

    test_collection = "test_collection"
    try:
        clear_collection(test_collection)
    except Exception:
        pass

    print(f"\n2. Storing chunks into ChromaDB...")
    sample_chunks = chunks[:5]
    add_documents_to_vector_store(sample_chunks, collection_name=test_collection)
    print("Chunks successfully stored & embedded!")

    test_query = "What is information retrieval in computing?"
    print(f"\n3. Querying vector store for: '{test_query}'")
    results = similarity_search_with_score(test_query, k=2, collection_name=test_collection)

    for idx, (doc, score) in enumerate(results, start=1):
        print(f"\n--- Match {idx} (Score: {score:.4f}) ---")
        print(doc.page_content[:300] + "...")
        print(f"Source: {doc.metadata.get('source')}")
