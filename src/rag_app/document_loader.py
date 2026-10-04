import os

os.environ.setdefault("USER_AGENT", "RagApp/1.0")

import bs4
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_url(url: str, clean_content: bool = True) -> List[Document]:
    
    if clean_content:
        bs_kwargs = {
            "parse_only": bs4.SoupStrainer(["p", "h1", "h2", "h3", "article", "section"])
        }
        loader = WebBaseLoader(url, bs_kwargs=bs_kwargs)
    else:
        loader = WebBaseLoader(url)
    
    return loader.load()



def load_pdf(file_path: str) -> List[Document]:
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    return docs


def split_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


if __name__ == "__main__":
    test_url = "https://en.wikipedia.org/wiki/Information_retrieval"
    print(f"Loading content from: {test_url}")
    
    docs = load_url(test_url)
    print(f"Loaded {len(docs)} document(s).")
    print(f"Total raw character count: {len(docs[0].page_content)}")

    print("\nSplitting into chunks (chunk_size=1000, chunk_overlap=200)...")
    chunks = split_documents(docs, chunk_size=1000, chunk_overlap=200)
    print(f"Generated {len(chunks)} chunks.")

    for i, chunk in enumerate(chunks[:2]):
        print(f"\n--- Chunk {i + 1} ({len(chunk.page_content)} chars) ---")
        print(chunk.page_content[:300] + "...")
        print(f"Metadata: {chunk.metadata}")
