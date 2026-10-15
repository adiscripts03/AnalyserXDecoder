# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Researchers, developers, knowledge workers, and technical analysts who need to query, verify, and synthesize information from lengthy technical PDFs, documentation, research papers, and web articles quickly and accurately.

## Product Purpose

Transform dense unstructured information into an interactive, conversational intelligence layer. AnalyserXDecoder eliminates manual skimming and synthesis while guaranteeing that every generated answer is strictly grounded in the ingested evidence with transparent citations.

## Positioning

"Any piece of evidence decoded to its very core!"
A zero-hallucination, dual-provider (Google Gemini & Mistral AI) RAG application with transparent source citations, chunk attribution, and rapid multi-source ingestion (live URLs and local PDFs).

## Operating Context

- **Environment:** Web application served by a FastAPI / Uvicorn backend, deployable to Render or Vercel.
- **Workflows:** 
  1. Ingesting content: Submitting a URL for web scraping or uploading a PDF document.
  2. Model selection: Selecting between Google Gemini and Mistral AI models.
  3. Querying & Synthesis: Asking natural language questions in an interactive chat interface.
  4. Evidence inspection: Reviewing cited sources, chunk excerpts, and document metadata.

## Capabilities and Constraints

- **Document Ingestion:** Automated text extraction from live URLs (BeautifulSoup4) and multi-page PDFs (PyPDF).
- **Chunking & Indexing:** Semantic chunking via RecursiveCharacterTextSplitter and vector indexing with ChromaDB.
- **Dual LLM Providers:** 
  - Google Gemini (`gemini-2.5-flash`, `gemini-2.0-flash`)
  - Mistral AI (`open-mistral-7b`, `mistral-small-latest`)
- **Frontend Stack:** Clean Vanilla HTML5, CSS3, and JavaScript (`static/index.html`, `static/style.css`, `static/app.js`) without heavy frontend framework runtimes.
- **Strict Grounding:** Responses are constrained by retrieved document context with footnote citations and source viewer modals.

## Brand Commitments

- **Product Name:** AnalyserXDecoder
- **Tagline:** Any piece of evidence decoded to its very core!
- **Identity & Voice:** Analytical, high-performance, transparent, and developer-friendly. Dark-mode first with dual theme support.

## Evidence on Hand

- Core backend pipeline in `src/rag_app/` (loaders, embeddings, vector store, server, RAG chain).
- Single-page frontend in `static/index.html`, `static/style.css`, and `static/app.js`.
- Architectural specifications and documentation in `README.md`.
- No customer testimonials or enterprise pricing claims exist; future work must not fabricate them.

## Product Principles

1. **Grounding Over Guesswork:** Answers must be firmly rooted in ingested sources; declare absence of evidence rather than hallucinating.
2. **Transparent Traceability:** Every factual claim must link directly to its source chunk, URL, or PDF page.
3. **Frictionless Ingestion:** Users should go from a raw URL or PDF to conversational Q&A in seconds.
4. **Focused Utility:** Keep the interface clean, highly responsive, and focused on synthesis and evidence inspection without unnecessary fluff.

## Accessibility & Inclusion

Target WCAG 2.1 AA standards for color contrast, keyboard navigability (tabs, inputs, model selectors), and visible focus rings in both light and dark themes.
