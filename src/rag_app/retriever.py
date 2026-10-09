from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from rag_app.vector_store import get_vector_store


def get_retriever(
    collection_name: str = "webpage_decoder",
    search_type: str = "similarity",
    k: int = 4,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
    score_threshold: Optional[float] = None,
) -> BaseRetriever:

    vector_store = get_vector_store(collection_name=collection_name)
    search_kwargs = {"k": k}

    if search_type == "mmr":
        search_kwargs["fetch_k"] = fetch_k
        search_kwargs["lambda_mult"] = lambda_mult
    elif search_type == "similarity_score_threshold":
        if score_threshold is None:
            score_threshold = 0.5
        search_kwargs["score_threshold"] = score_threshold

    return vector_store.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )


def get_similarity_retriever(
    collection_name: str = "webpage_decoder",
    k: int = 4,
) -> BaseRetriever:
    return get_retriever(
        collection_name=collection_name,
        search_type="similarity",
        k=k,
    )


def get_mmr_retriever(
    collection_name: str = "webpage_decoder",
    k: int = 4,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
) -> BaseRetriever:
    return get_retriever(
        collection_name=collection_name,
        search_type="mmr",
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
    )


def get_threshold_retriever(
    collection_name: str = "webpage_decoder",
    k: int = 4,
    score_threshold: float = 0.5,
) -> BaseRetriever:
    return get_retriever(
        collection_name=collection_name,
        search_type="similarity_score_threshold",
        k=k,
        score_threshold=score_threshold,
    )


def format_retrieved_documents(documents: List[Document]) -> str:
    formatted_chunks = []
    for idx, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "Unknown Source")
        title = doc.metadata.get("title", "")
        header = f"[Source {idx}: {source}" + (f" | {title}]" if title else "]")
        formatted_chunks.append(f"{header}\n{doc.page_content.strip()}")

    return "\n\n---\n\n".join(formatted_chunks)


if __name__ == "__main__":
    from rag_app.document_loader import load_url, split_documents
    from rag_app.vector_store import add_documents_to_vector_store, clear_collection

    sample_url = "https://en.wikipedia.org/wiki/Information_retrieval"
    test_collection = "retriever_demo_collection"

    print("==================================================")
    print("1. Ingesting sample webpage for retriever testing")
    print("==================================================")
    try:
        clear_collection(test_collection)
    except Exception:
        pass

    docs = load_url(sample_url)
    chunks = split_documents(docs, chunk_size=700, chunk_overlap=100)
    print(f"Loaded and chunked {len(chunks)} fragments. Storing first 8 into collection...")
    add_documents_to_vector_store(chunks[:8], collection_name=test_collection)

    query = "What are the common search queries and models in information retrieval?"
    print(f"\nQuery: '{query}'\n")

    print("--- 2. Testing Standard Similarity Retriever (k=2) ---")
    sim_retriever = get_similarity_retriever(collection_name=test_collection, k=2)
    sim_results = sim_retriever.invoke(query)
    for i, doc in enumerate(sim_results, start=1):
        print(f"Match #{i}: {doc.page_content[:150]}...\n")

    print("--- 3. Testing MMR Retriever (k=2, fetch_k=6, lambda_mult=0.5) ---")
    mmr_retriever = get_mmr_retriever(collection_name=test_collection, k=2, fetch_k=6, lambda_mult=0.5)
    mmr_results = mmr_retriever.invoke(query)
    for i, doc in enumerate(mmr_results, start=1):
        print(f"Match #{i}: {doc.page_content[:150]}...\n")

    print("--- 4. Formatted Context for LLM Prompt ---")
    formatted_context = format_retrieved_documents(mmr_results)
    print(formatted_context[:400] + "\n...")
    print("\nRetriever module verified successfully!")
