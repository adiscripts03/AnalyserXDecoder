# AnalyserXDecoder 🌐

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.4%2B-1C3C3C?logo=langchain&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?logo=google&logoColor=white)
![Mistral AI](https://img.shields.io/badge/Mistral_AI-Supported-FF7000)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Any piece of evidence decoded to its very core!**  
*A modern, high-performance Retrieval-Augmented Generation (RAG) platform that ingests web pages and PDF documents, creating an interactive conversational intelligence layer with grounded citations and zero hallucinations.*

[Overview](#-overview) •
[Features](#-key-features) •
[Architecture](#-architecture) •
[Quickstart](#-quickstart) •
[CLI Usage](#-cli-usage) •
[API Reference](#-rest-api-reference) •
[Deployment](#-deployment) •
[Configuration](#-configuration)

---

</div>

## 🚀 Overview

**AnalyserXDecoder** transforms how you interact with dense information. Instead of manually sifting through lengthy technical documentations, research papers, legal briefs, or articles, AnalyserXDecoder ingests sources, parses clean text, segments it into semantic chunks, and allows you to ask questions conversationally.

Answers are strictly grounded in your provided documents with citation footnotes, preventing LLM hallucinations and giving you full transparency into source excerpts.

---

## ✨ Key Features

- **Multi-Source Document Ingestion:**
  - **Live Web Scraping:** Extracts clean article text and metadata from URLs using BeautifulSoup4.
  - **PDF Document Parsing:** Extracts and cleans multi-page PDF documents with PyPDF.
- **Dual LLM Provider Support:**
  - **Google Gemini:** Supports `gemini-2.5-flash`, `gemini-2.0-flash`, and Google Generative AI embeddings.
  - **Mistral AI:** Supports `open-mistral-7b`, `mistral-small-latest`, and specialized Mistral models.
- **ChromaDB Vector Store:**
  - On-disk persistent vector database for fast similarity retrieval.
  - Multi-collection support with one-click collection wiping.
- **Advanced Retrieval Strategies:**
  - **Cosine Similarity:** Standard high-precision vector similarity matching.
  - **Maximal Marginal Relevance (MMR):** Balances relevance with document diversity to prevent redundant information.
- **Glassmorphic Web Interface:**
  - Responsive, modern frontend built with pure HTML5, CSS3, and JavaScript.
  - Native Dark/Light theme switching with persistence.
  - Interactive file dropzone for PDFs and instant URL indexing.
  - Expandable source citation drawers displaying exact matched chunks.
- **Full CLI & REPL Mode:**
  - Interactive terminal mode (`-i`) for rapid command-line question answering.
  - Scriptable batch queries and CLI automation options.
- **Production-Ready FastAPI Backend:**
  - CORS-enabled REST endpoints for seamless integration.
  - Automated health check endpoint (`/health`) for cloud monitoring.

---

## 🧠 Architecture

```text
       ┌──────────────────────┐      ┌──────────────────────┐
       │   Webpage / Article  │      │     PDF Document     │
       └──────────┬───────────┘      └──────────┬───────────┘
                  │                             │
                  ▼                             ▼
       [ BeautifulSoup4 Loader ]      [ PyPDF Parser Engine ]
                  │                             │
                  └──────────────┬──────────────┘
                                 ▼
            [ RecursiveCharacterTextSplitter ]
              (Chunk Size: 1000 | Overlap: 200)
                                 │
                                 ▼
             [ Google Gemini Vector Embeddings ]
              (3072-dimensional vector spaces)
                                 │
                                 ▼
             [ ChromaDB Persistent Vector Store ]
                                 │
     User Question               │
           │                     │
           ▼                     ▼
     [ Vector Search: Cosine Similarity / MMR ]
           │
           ▼
     [ Augmented Context + Strict Citation Prompt ]
           │
           ▼
     [ LLM Generation: Gemini / Mistral AI ]
           │
           ▼
     ✅ Grounded Answer with Source Footnotes ([Source 1], [Source 2])
```

---

## 📁 Repository Structure

```text
AnalyserXDecoder/
├── main.py                  # Server and CLI launcher entrypoint
├── deploy_render.py         # Automated Render cloud deployment script
├── render.yaml              # Render Blueprint specification (Free tier)
├── vercel.json              # Vercel deployment configuration
├── requirements.txt         # Production pip dependencies
├── pyproject.toml           # Project metadata and uv dependencies
├── src/
│   └── rag_app/
│       ├── __init__.py
│       ├── server.py        # FastAPI application & REST API routes
│       ├── main.py          # Core RAG pipeline, chain orchestration & CLI
│       ├── retriever.py     # Similarity and MMR retrieval strategies
│       ├── vector_store.py  # ChromaDB persistent collection management
│       ├── document_loader.py # Web scraping & PDF text extraction
│       ├── embeddings.py    # Google Gemini embedding wrappers
│       └── similarity.py    # Cosine distance & similarity helpers
├── static/
│   ├── index.html           # Modern glassmorphic Web UI
│   ├── style.css            # Dark/light design system styling
│   └── app.js               # Reactive frontend controller
└── vectorstore/             # Local ChromaDB persistent database files
```

---

## ⚡ Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/adiscripts03/AnalyserXDecoder.git
cd AnalyserXDecoder
```

### 2. Environment Setup

You can use either [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip` with `venv`:

#### Using `uv`:
```bash
uv sync
```

#### Using `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and fill in your API credentials:
```env
# Google Gemini API Key (https://aistudio.google.com/)
GOOGLE_API_KEY=your_gemini_api_key_here

# Mistral AI API Key (https://console.mistral.ai/)
MISTRAL_API_KEY=your_mistral_api_key_here

# Default Provider ("gemini" or "mistral")
LLM_PROVIDER=gemini
```

### 4. Run the Web Application

Launch the FastAPI web server:
```bash
python main.py
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 💻 CLI Usage

AnalyserXDecoder includes a rich CLI for terminal enthusiasts and automation workflows.

### 1. Interactive Terminal Mode
Start an interactive chat session with your indexed knowledge base:
```bash
python main.py -i
```

### 2. Ingest Sources from the Terminal
- **Ingest a Web Page:**
  ```bash
  python main.py --url "https://en.wikipedia.org/wiki/Artificial_intelligence"
  ```
- **Ingest a PDF Document:**
  ```bash
  python main.py --pdf "/path/to/document.pdf"
  ```

### 3. Query Directly via CLI
- **Query using Gemini (Default):**
  ```bash
  python main.py -q "What are the primary findings in the document?"
  ```
- **Query using Mistral AI:**
  ```bash
  python main.py -q "Summarize the key points" --provider mistral
  ```
- **Use Maximal Marginal Relevance (MMR) for diverse retrieval:**
  ```bash
  python main.py -q "Compare the different approaches" --search-type mmr -k 5
  ```

### 4. Clear Vector Store
```bash
python main.py --clear
```

---

## 🌐 REST API Reference

The FastAPI server exposes clean endpoints for building custom integrations or mobile apps:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web interface (`index.html`) |
| `GET` | `/health` | Health check endpoint for uptime monitoring |
| `GET` | `/api/status` | Current server configuration, active keys, and providers |
| `POST` | `/api/ingest/url` | Ingests and embeds text from a webpage URL |
| `POST` | `/api/ingest/pdf` | Accepts multipart `file` upload and embeds a PDF |
| `POST` | `/api/query` | Generates a grounded response with source citations |
| `POST` | `/api/clear` | Clears and resets the ChromaDB vector collection |

### Example Query Request (`POST /api/query`)

```json
{
  "question": "What is the core architecture described?",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "search_type": "similarity",
  "k": 4
}
```

### Example Response

```json
{
  "success": true,
  "answer": "The core architecture consists of an ingestion pipeline followed by ChromaDB vector storage and Gemini flash generation [Source 1].",
  "documents": [
    {
      "page_content": "Detailed excerpt from the document...",
      "metadata": { "source": "https://example.com", "chunk": 0 }
    }
  ],
  "provider": "gemini"
}
```

---

## ☁️ Deployment

### Deploying to Render (Recommended)

This repository includes a pre-configured [render.yaml](render.yaml) file set to Render's **Free Tier**.

#### Option A: 1-Click Web Dashboard
1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your GitHub repository: `adiscripts03/AnalyserXDecoder`.
4. Configure:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** `Free`
5. Add your environment variables (`GOOGLE_API_KEY`, `MISTRAL_API_KEY`, `LLM_PROVIDER=gemini`).
6. Click **Deploy Web Service**!

#### Option B: Automated API Script
If you have a card verified on your Render account:
```bash
python deploy_render.py
```

### Deploying to Vercel
Configuration is included in [vercel.json](vercel.json).
```bash
npx vercel
```

---

## ⚙️ Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Conditional | - | Google Gemini API key from AI Studio |
| `MISTRAL_API_KEY` | Conditional | - | Mistral AI API key from console.mistral.ai |
| `LLM_PROVIDER` | No | `gemini` | Default model provider (`gemini` or `mistral`) |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Specific Gemini model identifier |
| `MISTRAL_MODEL` | No | `open-mistral-7b` | Specific Mistral model identifier |
| `PORT` | No | `8000` | Port for the FastAPI web server |
| `ENVIRONMENT` | No | `development` | Server runtime environment mode |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
