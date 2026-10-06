document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const providerSelect = document.getElementById("providerSelect");
  const modelSelect = document.getElementById("modelSelect");
  const activeModelBadge = document.getElementById("activeModelBadge");
  const urlTabBtn = document.querySelector('[data-tab="urlTab"]');
  const pdfTabBtn = document.querySelector('[data-tab="pdfTab"]');
  const urlTab = document.getElementById("urlTab");
  const pdfTab = document.getElementById("pdfTab");
  const urlInput = document.getElementById("urlInput");
  const indexUrlBtn = document.getElementById("indexUrlBtn");
  const dropzone = document.getElementById("dropzone");
  const pdfFileInput = document.getElementById("pdfFileInput");
  const fileNamePreview = document.getElementById("fileNamePreview");
  const indexPdfBtn = document.getElementById("indexPdfBtn");
  const searchTypeSelect = document.getElementById("searchTypeSelect");
  const kChunksRange = document.getElementById("kChunksRange");
  const kValLabel = document.getElementById("kValLabel");
  const sourcesList = document.getElementById("sourcesList");
  const sourceCountBadge = document.getElementById("sourceCountBadge");
  const clearStoreBtn = document.getElementById("clearStoreBtn");
  const messagesContainer = document.getElementById("messagesContainer");
  const emptyState = document.getElementById("emptyState");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const toast = document.getElementById("toast");

  let indexedSources = [];
  let selectedPdfFile = null;

  // Model Options Mapping
  const MODEL_OPTIONS = {
    gemini: [
      { id: "gemini-3.5-flash", name: "Gemini 3.5 Flash (Fast & Grounded)" },
      { id: "gemini-3.8-flash", name: "Gemini 3.8 Flash (Latest)" },
      { id: "gemini-flash-latest", name: "Gemini Flash Latest" },
    ],
    mistral: [
      { id: "open-mistral-7b", name: "Open Mistral 7B (Fast & Free Tier)" },
      { id: "mistral-small-latest", name: "Mistral Small Latest" },
      { id: "codestral-latest", name: "Codestral Latest" },
    ],
  };

  // Toast Helper
  function showToast(message, type = "success") {
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
      toast.className = "toast";
    }, 3500);
  }

  // Update Model Select
  function updateModelOptions() {
    const provider = providerSelect.value;
    const models = MODEL_OPTIONS[provider] || [];
    modelSelect.innerHTML = "";
    models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.name;
      modelSelect.appendChild(opt);
    });
    updateBadge();
  }

  function updateBadge() {
    const providerName = providerSelect.options[providerSelect.selectedIndex].text;
    const modelId = modelSelect.value;
    activeModelBadge.textContent = `${providerName} (${modelId})`;
  }

  providerSelect.addEventListener("change", updateModelOptions);
  modelSelect.addEventListener("change", updateBadge);
  updateModelOptions();

  // Tab Switching
  [urlTabBtn, pdfTabBtn].forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(target).classList.add("active");
    });
  });

  // K Slider
  kChunksRange.addEventListener("input", (e) => {
    kValLabel.textContent = e.target.value;
  });

  // PDF File Dropzone
  dropzone.addEventListener("click", () => pdfFileInput.click());
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--primary)";
  });
  dropzone.addEventListener("dragleave", () => {
    dropzone.style.borderColor = "var(--border-color)";
  });
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--border-color)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handlePdfSelected(e.dataTransfer.files[0]);
    }
  });
  pdfFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handlePdfSelected(e.target.files[0]);
    }
  });

  function handlePdfSelected(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showToast("Please select a valid .pdf file", "error");
      return;
    }
    selectedPdfFile = file;
    fileNamePreview.textContent = `📄 ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    indexPdfBtn.disabled = false;
  }

  // Refresh Sources UI
  function renderSources() {
    sourceCountBadge.textContent = indexedSources.length;
    if (indexedSources.length === 0) {
      sourcesList.innerHTML = `<div class="empty-sources">No sources indexed in this session.</div>`;
      return;
    }
    sourcesList.innerHTML = indexedSources
      .map(
        (src, idx) => `
        <div class="source-item" title="${src}">
          <span class="source-item-icon">📌</span>
          <span class="source-item-text">${idx + 1}. ${escapeHtml(src)}</span>
        </div>
      `
      )
      .join("");
  }

  // Ingest URL Action
  indexUrlBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      showToast("Please enter a valid URL", "error");
      return;
    }

    indexUrlBtn.disabled = true;
    indexUrlBtn.innerHTML = `<span>Indexing...</span>`;

    try {
      const res = await fetch("/api/ingest/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Failed to index URL");
      }
      showToast(`Successfully indexed ${data.chunks} chunks!`, "success");
      if (!indexedSources.includes(url)) {
        indexedSources.push(url);
        renderSources();
      }
      urlInput.value = "";
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      indexUrlBtn.disabled = false;
      indexUrlBtn.innerHTML = `<span>Index Webpage</span>`;
    }
  });

  // Ingest PDF Action
  indexPdfBtn.addEventListener("click", async () => {
    if (!selectedPdfFile) return;

    indexPdfBtn.disabled = true;
    indexPdfBtn.innerHTML = `<span>Uploading & Indexing...</span>`;

    const formData = new FormData();
    formData.append("file", selectedPdfFile);

    try {
      const res = await fetch("/api/ingest/pdf", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Failed to index PDF");
      }
      showToast(`Successfully indexed ${data.chunks} chunks from ${selectedPdfFile.name}!`, "success");
      if (!indexedSources.includes(selectedPdfFile.name)) {
        indexedSources.push(selectedPdfFile.name);
        renderSources();
      }
      selectedPdfFile = null;
      fileNamePreview.textContent = "";
      pdfFileInput.value = "";
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      indexPdfBtn.disabled = false;
      indexPdfBtn.innerHTML = `<span>Index PDF</span>`;
    }
  });

  // Clear Store Action
  clearStoreBtn.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear all indexed knowledge from the vector store?")) {
      return;
    }
    clearStoreBtn.disabled = true;
    try {
      const res = await fetch("/api/clear", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Failed to clear collection");
      }
      indexedSources = [];
      renderSources();
      showToast("Knowledge base cleared successfully", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      clearStoreBtn.disabled = false;
    }
  });

  // Quick Prompt Click
  document.querySelectorAll(".quick-prompt-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      chatInput.value = btn.dataset.prompt;
      chatInput.focus();
    });
  });

  // Chat Submission
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Remove empty state if present
    if (emptyState) {
      emptyState.style.display = "none";
    }

    // Append User Message
    appendMessage("user", query);
    chatInput.value = "";
    chatInput.disabled = true;
    sendBtn.disabled = true;

    // Append Pending Assistant Bubble
    const pendingId = "pending-" + Date.now();
    appendLoadingMessage(pendingId);

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: query,
          provider: providerSelect.value,
          model: modelSelect.value,
          search_type: searchTypeSelect.value,
          k: parseInt(kChunksRange.value, 10),
        }),
      });

      const data = await res.json();
      removeMessage(pendingId);

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to query RAG model");
      }

      appendMessage("assistant", data.answer, data.documents || []);
    } catch (err) {
      removeMessage(pendingId);
      appendMessage("assistant", `⚠️ Error: ${err.message}`);
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  });

  // Render Messages
  function appendMessage(role, content, documents = []) {
    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const avatar = document.createElement("div");
    avatar.className = `avatar ${role}`;
    avatar.textContent = role === "user" ? "You" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = formatMarkdown(content);

    // Citations Accordion
    if (role === "assistant" && documents && documents.length > 0) {
      const accordion = document.createElement("div");
      accordion.className = "sources-accordion";

      const header = document.createElement("div");
      header.className = "sources-accordion-header";
      header.innerHTML = `<span>📚 Retrieved Sources (${documents.length})</span><span>▾</span>`;
      header.addEventListener("click", () => {
        accordion.classList.toggle("open");
        header.querySelector("span:last-child").textContent = accordion.classList.contains("open") ? "▴" : "▾";
      });

      const body = document.createElement("div");
      body.className = "sources-accordion-content";
      body.innerHTML = documents
        .map((doc, idx) => {
          const meta = doc.metadata || {};
          const source = meta.source || "Unknown Source";
          const title = meta.title ? ` (${meta.title})` : "";
          const snippet = doc.page_content || "";
          return `
            <div class="source-card">
              <div class="source-card-header">[Source ${idx + 1}] ${escapeHtml(source)}${escapeHtml(title)}</div>
              <div class="source-card-snippet">${escapeHtml(snippet)}</div>
            </div>
          `;
        })
        .join("");

      accordion.appendChild(header);
      accordion.appendChild(body);
      bubble.appendChild(accordion);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendLoadingMessage(id) {
    const row = document.createElement("div");
    row.id = id;
    row.className = "message-row assistant";

    const avatar = document.createElement("div");
    avatar.className = "avatar assistant";
    avatar.textContent = "AI";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = `
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesContainer.appendChild(row);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  // Formatting helpers
  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, "<code style='background:#f1f5f9;padding:2px 4px;border-radius:4px;font-size:0.85em;'>$1</code>");
    // Line breaks to <br>
    html = html.replace(/\n\n/g, "</p><p style='margin-top:8px;'>");
    html = html.replace(/\n/g, "<br>");
    return `<p>${html}</p>`;
  }
});
