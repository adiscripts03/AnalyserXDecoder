import os
import re
from typing import List
from pathlib import Path

os.environ.setdefault("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

import bs4
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

MAX_CHUNKS_PER_INGEST = int(os.getenv("MAX_CHUNKS_PER_INGEST", "100"))
MIN_CHUNK_LENGTH = 30


def _clean_text(text: str) -> str:
    """Removes null bytes, excessive whitespace, and abnormal control characters."""
    if not text:
        return ""
    # Strip null bytes that break ChromaDB/SQLite
    text = text.replace("\x00", " ")
    # Replace non-breaking spaces and tabs
    text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple inline spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def load_url(url: str, clean_content: bool = True) -> List[Document]:
    """Loads and extracts clean, readable text from a webpage URL."""
    import urllib.request

    headers = {
        "User-Agent": os.environ["USER_AGENT"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        # Fallback to langchain WebBaseLoader if direct urllib request fails
        from langchain_community.document_loaders import WebBaseLoader
        loader = WebBaseLoader(url)
        return loader.load()

    soup = bs4.BeautifulSoup(html, "html.parser")

    # Extract page title
    page_title = ""
    if soup.title and soup.title.string:
        page_title = soup.title.string.strip()

    if clean_content:
        # Remove noisy boilerplates, navigation, scripts, ads, footers
        noise_selectors = [
            "script", "style", "noscript", "nav", "footer", "header",
            "aside", "svg", "form", "iframe", ".navbox", ".reflist",
            ".reference", ".mw-editsection", "#toc", ".sidebar",
            ".footer", ".menu", ".advertisement", ".cookie-banner"
        ]
        for selector in noise_selectors:
            for el in soup.select(selector):
                el.decompose()

    # Find the main body or article container
    content_element = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"content|main|article|bodyContent", re.I))
        or soup.find(class_=re.compile(r"content|main|article|post|body", re.I))
        or soup.body
        or soup
    )

    extracted_text = content_element.get_text(separator="\n", strip=True) if content_element else ""
    cleaned_text = _clean_text(extracted_text)

    # Fallback to full body if smart extraction is too short (< 100 chars)
    if len(cleaned_text) < 100 and soup.body:
        cleaned_text = _clean_text(soup.body.get_text(separator="\n", strip=True))

    if not cleaned_text:
        return []

    metadata = {
        "source": url,
        "title": page_title or url,
    }
    return [Document(page_content=cleaned_text, metadata=metadata)]


def load_pdf(file_path: str) -> List[Document]:
    """Loads and sanitizes text from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found at: {file_path}")

    loader = PyPDFLoader(str(path))
    raw_docs = loader.load()

    cleaned_docs = []
    for doc in raw_docs:
        text = _clean_text(doc.page_content)
        # Drop empty pages (blank pages or cover images without text)
        if len(text) >= MIN_CHUNK_LENGTH:
            doc.page_content = text
            # Sanitize metadata values
            sanitized_meta = {}
            for k, v in doc.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    sanitized_meta[k] = v
                elif v is not None:
                    sanitized_meta[k] = str(v)
            doc.metadata = sanitized_meta
            cleaned_docs.append(doc)

    return cleaned_docs


def split_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """Splits documents into semantic chunks, sanitizing and filtering invalid chunks."""
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    raw_chunks = text_splitter.split_documents(documents)

    valid_chunks: List[Document] = []
    for i, chunk in enumerate(raw_chunks):
        cleaned = _clean_text(chunk.page_content)
        # CRUCIAL: Exclude empty chunks or trivial fragments that cause Gemini 400 INVALID_ARGUMENT
        if len(cleaned) < MIN_CHUNK_LENGTH:
            continue

        chunk.page_content = cleaned
        # Ensure metadata is clean and valid for ChromaDB
        meta = {
            "source": str(chunk.metadata.get("source", "unknown")),
            "chunk_index": i,
        }
        for k, v in chunk.metadata.items():
            if k not in meta and isinstance(v, (str, int, float, bool)):
                meta[k] = v
        chunk.metadata = meta
        valid_chunks.append(chunk)

    # Prevent quota exhaustion: cap to MAX_CHUNKS_PER_INGEST if massive document
    if len(valid_chunks) > MAX_CHUNKS_PER_INGEST:
        print(f"⚠️ Document produced {len(valid_chunks)} chunks; capping to top {MAX_CHUNKS_PER_INGEST} chunks to protect API quota.")
        valid_chunks = valid_chunks[:MAX_CHUNKS_PER_INGEST]

    return valid_chunks
