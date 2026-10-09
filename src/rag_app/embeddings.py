import os
import re
import time
import logging
from typing import List, Optional
from dotenv import load_dotenv

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

logger = logging.getLogger("rag_app.embeddings")

DEFAULT_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")


class ResilientGoogleEmbeddings(Embeddings):
    """Robust wrapper for Google Generative AI Embeddings with batching,
    sanitization against empty parts, and exponential backoff retry on rate limits (429)."""

    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = 20,
        max_retries: int = 4,
        base_delay: float = 3.0,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        self.client = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key or os.getenv("GOOGLE_API_KEY"),
        )

    def _sanitize_texts(self, texts: List[str]) -> List[str]:
        """Ensures every text is clean, non-empty, and free of null bytes.
        Prevents Google API 400 INVALID_ARGUMENT (empty Part error)."""
        sanitized = []
        for t in texts:
            if not t:
                cleaned = "[empty chunk]"
            else:
                cleaned = t.replace("\x00", " ").strip()
                if not cleaned:
                    cleaned = "[empty chunk]"
            sanitized.append(cleaned)
        return sanitized

    def _extract_retry_delay(self, error_message: str, attempt: int) -> float:
        """Parses recommended retry delay from Google API error response if available."""
        # Check for 'retryDelay': '28s' or 'retry in 28.5s'
        match = re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", error_message, re.IGNORECASE)
        if match:
            try:
                delay = float(match.group(1)) + 1.0
                return min(delay, 45.0)
            except ValueError:
                pass
        return self.base_delay * (2 ** attempt)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of documents in safe batches with rate-limit retries."""
        if not texts:
            return []

        clean_texts = self._sanitize_texts(texts)
        all_embeddings: List[List[float]] = []

        total_batches = (len(clean_texts) + self.batch_size - 1) // self.batch_size

        for b_idx in range(0, len(clean_texts), self.batch_size):
            batch = clean_texts[b_idx : b_idx + self.batch_size]
            current_batch_num = (b_idx // self.batch_size) + 1

            for attempt in range(self.max_retries):
                try:
                    embeddings_batch = self.client.embed_documents(batch)
                    all_embeddings.extend(embeddings_batch)
                    
                    # Pacing between batches to avoid 100 requests/min quota spike
                    if b_idx + self.batch_size < len(clean_texts):
                        time.sleep(0.4)
                    break
                except Exception as e:
                    err_msg = str(e)
                    is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                    
                    if is_rate_limit and attempt < self.max_retries - 1:
                        wait_time = self._extract_retry_delay(err_msg, attempt)
                        logger.warning(
                            f"⏳ Rate limit on batch {current_batch_num}/{total_batches}. "
                            f"Waiting {wait_time:.1f}s before retry (attempt {attempt + 1}/{self.max_retries})..."
                        )
                        print(f"⏳ Rate limit encountered. Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Failed to embed batch {current_batch_num}: {err_msg}")
                        raise e

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single user query."""
        clean_text = (text or "").replace("\x00", " ").strip()
        if not clean_text:
            clean_text = "query"

        for attempt in range(self.max_retries):
            try:
                return self.client.embed_query(clean_text)
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < self.max_retries - 1:
                    wait_time = self._extract_retry_delay(err_msg, attempt)
                    print(f"⏳ Rate limit on query. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise e


def get_embedding_function() -> ResilientGoogleEmbeddings:
    """Returns an instance of ResilientGoogleEmbeddings."""
    return ResilientGoogleEmbeddings()


if __name__ == "__main__":
    emb = get_embedding_function()
    print("Testing resilient embeddings on sample text...")
    vec = emb.embed_query("Information retrieval test")
    print(f"✅ Success! Vector dimension: {len(vec)}")