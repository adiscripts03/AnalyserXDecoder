import os
import sys
import tempfile
from pathlib import Path
from typing import List

# Ensure project root and src directory are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
for p in [str(ROOT_DIR), str(SRC_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
from dotenv import load_dotenv

from rag_app.document_loader import load_url, load_pdf, split_documents
from rag_app.vector_store import (
    add_documents_to_vector_store,
    clear_collection,
    get_vector_store,
)
from rag_app.retriever import get_retriever, format_retrieved_documents
from rag_app.main import (
    answer_query,
    build_rag_chain,
    DEFAULT_COLLECTION,
    DEFAULT_PROVIDER,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_MISTRAL_MODEL,
)

load_dotenv()

st.set_page_config(
    page_title="WebpageDecoder",
    page_icon="🌐",
    layout="wide",
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed_sources" not in st.session_state:
    st.session_state.indexed_sources = []


# Sidebar: Configuration & Data Ingestion
with st.sidebar:
    st.title("Configuration & Ingestion")

    # Provider and Model Selection
    st.subheader("LLM Provider")
    provider_option = st.selectbox(
        "Select Provider",
        options=["Gemini", "Mistral"],
        index=0 if DEFAULT_PROVIDER == "gemini" else 1,
    )

    if provider_option == "Gemini":
        has_key = bool(os.getenv("GOOGLE_API_KEY"))
        if not has_key:
            st.warning("GOOGLE_API_KEY not found in .env")
        model_options = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]
        selected_model = st.selectbox("Model", options=model_options, index=0)
    else:
        has_key = bool(os.getenv("MISTRAL_API_KEY"))
        if not has_key:
            st.warning("MISTRAL_API_KEY not found in .env")
        model_options = ["open-mistral-7b", "mistral-small-latest", "codestral-latest"]
        selected_model = st.selectbox("Model", options=model_options, index=0)

    st.divider()

    st.subheader("Add Content")
    ingest_tab1, ingest_tab2 = st.tabs(["Webpage URL", "PDF File"])

    with ingest_tab1:
        url_input = st.text_input("Enter URL", placeholder="https://example.com/article")
        if st.button("Index Webpage", use_container_width=True):
            if not url_input.strip():
                st.error("Please enter a valid URL.")
            else:
                with st.spinner("Fetching and indexing webpage..."):
                    try:
                        docs = load_url(url_input.strip())
                        if docs:
                            chunks = split_documents(docs)
                            add_documents_to_vector_store(chunks, collection_name=DEFAULT_COLLECTION)
                            if url_input.strip() not in st.session_state.indexed_sources:
                                st.session_state.indexed_sources.append(url_input.strip())
                            st.success(f"Indexed {len(chunks)} chunks successfully.")
                        else:
                            st.error("Could not extract readable text from the URL.")
                    except Exception as e:
                        st.error(f"Failed to ingest URL: {e}")

    with ingest_tab2:
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if st.button("Index PDF", use_container_width=True):
            if uploaded_pdf is None:
                st.error("Please select a PDF file.")
            else:
                with st.spinner("Parsing and indexing PDF..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(uploaded_pdf.read())
                            tmp_path = tmp_file.name

                        docs = load_pdf(tmp_path)
                        os.unlink(tmp_path)

                        if docs:
                            chunks = split_documents(docs)
                            add_documents_to_vector_store(chunks, collection_name=DEFAULT_COLLECTION)
                            if uploaded_pdf.name not in st.session_state.indexed_sources:
                                st.session_state.indexed_sources.append(uploaded_pdf.name)
                            st.success(f"Indexed {len(chunks)} chunks from {uploaded_pdf.name}.")
                        else:
                            st.error("Could not extract readable text from the PDF.")
                    except Exception as e:
                        st.error(f"Failed to ingest PDF: {e}")

    st.divider()

    # Retrieval options
    st.subheader("Retrieval Strategy")
    search_type = st.selectbox(
        "Search Type",
        options=["similarity", "mmr"],
        format_func=lambda x: "Cosine Similarity" if x == "similarity" else "MMR (Diverse Chunks)",
    )
    k_chunks = st.slider("Chunks to Retrieve (k)", min_value=1, max_value=10, value=4)

    st.divider()

    # Indexed Sources Summary
    st.subheader("Indexed Sources")
    if st.session_state.indexed_sources:
        for idx, src in enumerate(st.session_state.indexed_sources, start=1):
            st.caption(f"{idx}. {src}")
    else:
        st.caption("No sources indexed in this session yet.")

    # Reset button
    if st.button("Clear Vector Store", type="secondary", use_container_width=True):
        try:
            clear_collection(DEFAULT_COLLECTION)
            st.session_state.indexed_sources = []
            st.session_state.messages = []
            st.success("Vector store and chat history cleared.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to clear store: {e}")


# Main Content Area
st.title("WebpageDecoder")
st.caption(f"Grounded RAG Q&A using **{provider_option}** ({selected_model}) over indexed documents.")

# Render previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Retrieved Sources"):
                for idx, src_doc in enumerate(message["sources"], start=1):
                    src_title = src_doc.get("title", "")
                    src_path = src_doc.get("source", "Unknown")
                    header = f"Source {idx}: {src_path}" + (f" ({src_title})" if src_title else "")
                    st.markdown(f"**{header}**")
                    st.text(src_doc.get("content", "").strip())

# Chat input
if prompt := st.chat_input("Ask a question about the indexed content..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner(f"Retrieving context & answering with {provider_option}..."):
            try:
                result = answer_query(
                    question=prompt,
                    collection_name=DEFAULT_COLLECTION,
                    search_type=search_type,
                    k=k_chunks,
                    provider=provider_option.lower(),
                    model_name=selected_model,
                )
                answer_text = result["answer"]
                documents = result.get("documents", [])

                st.markdown(answer_text)

                sources_payload = []
                if documents:
                    with st.expander("Retrieved Sources"):
                        for idx, doc in enumerate(documents, start=1):
                            src_meta = doc.metadata or {}
                            source_item = {
                                "source": src_meta.get("source", "Unknown"),
                                "title": src_meta.get("title", ""),
                                "content": doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""),
                            }
                            sources_payload.append(source_item)
                            header = f"Source {idx}: {source_item['source']}" + (
                                f" ({source_item['title']})" if source_item["title"] else ""
                            )
                            st.markdown(f"**{header}**")
                            st.text(source_item["content"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "sources": sources_payload,
                })

            except Exception as e:
                error_msg = f"An error occurred: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })