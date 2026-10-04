# WebpageDecoder (Wikipedia of Webpages) 🌐

> **Webpages decoded to their very core!**  
> A Retrieval-Augmented Generation (RAG) application that allows users to provide any webpage URL or document (PDF) and converse with it using Google Gemini and ChromaDB.

---

## 🚀 Overview

**WebpageDecoder** is an AI-powered document intelligence app. Instead of manually reading through lengthy articles, research papers, or documentation, WebpageDecoder ingests the source, extracts clean text, splits it into semantic chunks, and allows you to query it conversationally with grounded, hallucination-free answers.

---

## 🛠️ Tech Stack

- **Framework**: [Streamlit](https://streamlit.io/)
- **Orchestration**: [LangChain](https://www.langchain.com/)
- **LLM & Embeddings**: Google Gemini (`models/gemini-embedding-001`, Gemini 1.5 / 2.0 Flash)
- **Vector Database**: [ChromaDB](https://www.trychroma.com/)
- **Document Extractors**: [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) (Web scraping) & [pypdf](https://pypdf.readthedocs.io/) (PDF parsing)
- **Package & Environment Manager**: [uv](https://github.com/astral-sh/uv)

---

## 🧠 How It Works (RAG Pipeline)

```text
[ Webpage URL / PDF ]
          │
          ▼
   1. Document Loader (BeautifulSoup / PyPDF)
          │
          ▼
   2. Semantic Chunking (RecursiveCharacterTextSplitter)
          │
          ▼
   3. Vector Embeddings (Gemini Embeddings - 3072 dims)
          │
          ▼
   4. Vector Storage (ChromaDB)
          │
          ▼
   5. Similarity Search (Cosine Similarity on User Question)
          │
          ▼
   6. Augmented Prompt + Gemini LLM ──► Accurate Answer with Citations
```

---

## 📋 Project Roadmap

- [x] Project environment initialization using `uv`
- [x] Google Gemini Embeddings integration (`embeddings.py`)
- [x] Semantic similarity & cosine distance evaluation (`similarity.py`)
- [x] Document loader module for URLs and PDFs (`document_loader.py`)
- [ ] ChromaDB local vector store persistence (`vectorstore/`)
- [ ] RAG retrieval chain using Gemini LLM
- [ ] Full Streamlit user interface with chat history & source inspection

---

## ⚡ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/adiscripts03/WebpageDecoder.git
cd WebpageDecoder
```

### 2. Set up environment & dependencies
Make sure you have [uv](https://github.com/astral-sh/uv) installed, then run:
```bash
uv sync
```

### 3. Configure API Key
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Open `.env` and add your Google Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```
*(Get a key from [Google AI Studio](https://aistudio.google.com/)).*

---

## 🧪 Testing Current Modules

- **Test Embeddings & API Connection:**
  ```bash
  python src/rag_app/embeddings.py
  ```

- **Test Cosine Similarity Computation:**
  ```bash
  python src/rag_app/similarity.py
  ```

- **Test Web Scraping & Chunking:**
  ```bash
  python src/rag_app/document_loader.py
  ```

- **Run the Streamlit App:**
  ```bash
  streamlit run src/rag_app/app.py
  ```
