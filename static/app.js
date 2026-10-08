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
  const indexSuccessBanner = document.getElementById("indexSuccessBanner");
  const indexSuccessText = document.getElementById("indexSuccessText");

  let indexedSources = [];
  let selectedPdfFile = null;
  let bannerTimeout = null;

  // ----------------------------------------------------
  // Theme Switcher Logic
  // ----------------------------------------------------
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch (e) {}

    document.querySelectorAll(".theme-segment-btn").forEach((btn) => {
      const val = btn.getAttribute("data-theme-val");
      if (val === theme) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  const savedTheme = localStorage.getItem("theme") || "dark";
  applyTheme(savedTheme);

  document.querySelectorAll(".theme-segment-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const themeVal = btn.getAttribute("data-theme-val");
      if (themeVal) {
        applyTheme(themeVal);
      }
    });
  });

  // ----------------------------------------------------
  // Model Provider Mapping
  // ----------------------------------------------------
  const MODEL_OPTIONS = {
    gemini: [
      { id: "gemini-3.5-flash", name: "Gemini 3.5 Flash" },
      { id: "gemini-3.8-flash", name: "Gemini 3.8 Flash" },
      { id: "gemini-flash-latest", name: "Gemini Flash Latest" },
    ],
    mistral: [
      { id: "open-mistral-7b", name: "Mistral 7B" },
      { id: "mistral-small-latest", name: "Mistral Small" },
      { id: "codestral-latest", name: "Codestral" },
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

  // Green Inline Confirmation Helper
  function showGreenConfirmation(message) {
    if (!indexSuccessBanner || !indexSuccessText) return;
    indexSuccessText.textContent = message;
    indexSuccessBanner.style.display = "flex";

    if (bannerTimeout) clearTimeout(bannerTimeout);
    bannerTimeout = setTimeout(() => {
      indexSuccessBanner.style.display = "none";
    }, 8000);
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
    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
    const modelText = selectedOption ? selectedOption.text : modelSelect.value;
    activeModelBadge.textContent = modelText;
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
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
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
      showToast("Please select a valid PDF file", "error");
      return;
    }
    selectedPdfFile = file;
    fileNamePreview.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    indexPdfBtn.disabled = false;
  }

  // Refresh Sources UI
  function renderSources() {
    sourceCountBadge.textContent = indexedSources.length;
    if (indexedSources.length === 0) {
      sourcesList.innerHTML = `<div class="empty-sources">No sources indexed yet.</div>`;
      return;
    }
    sourcesList.innerHTML = indexedSources
      .map(
        (src, idx) => `
        <div class="source-item" title="${escapeHtml(src.name)}">
          <span class="source-index">${idx + 1}</span>
          <span class="source-item-text">${escapeHtml(src.name)}</span>
          <span class="source-chunk-tag">✓ ${src.chunks} chunks</span>
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

      // 1. Show Green Inline Banner
      showGreenConfirmation(`✓ Indexed ${data.chunks} chunks successfully!`);

      // 2. Toast in Green
      showToast(`✓ Successfully indexed ${data.chunks} chunks!`, "success");

      // 3. Button turns vibrant green temporarily
      indexUrlBtn.classList.add("btn-success");
      indexUrlBtn.innerHTML = `<span>✓ Done! (${data.chunks} chunks)</span>`;
      setTimeout(() => {
        indexUrlBtn.classList.remove("btn-success");
        indexUrlBtn.innerHTML = `<span>Index URL</span>`;
      }, 4000);

      // 4. Update Sources list with green chunk badge
      const existing = indexedSources.find((s) => s.name === url);
      if (existing) {
        existing.chunks = data.chunks;
      } else {
        indexedSources.push({ name: url, chunks: data.chunks });
      }
      renderSources();
      urlInput.value = "";
    } catch (err) {
      showToast(err.message, "error");
      indexUrlBtn.innerHTML = `<span>Index URL</span>`;
    } finally {
      indexUrlBtn.disabled = false;
    }
  });

  // Ingest PDF Action
  indexPdfBtn.addEventListener("click", async () => {
    if (!selectedPdfFile) return;

    const currentFileName = selectedPdfFile.name;
    indexPdfBtn.disabled = true;
    indexPdfBtn.innerHTML = `<span>Indexing...</span>`;

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

      // 1. Show Green Inline Banner
      showGreenConfirmation(`✓ Indexed ${data.chunks} chunks from ${currentFileName}!`);

      // 2. Toast in Green
      showToast(`✓ Successfully indexed ${data.chunks} chunks!`, "success");

      // 3. Button turns vibrant green temporarily
      indexPdfBtn.classList.add("btn-success");
      indexPdfBtn.innerHTML = `<span>✓ Done! (${data.chunks} chunks)</span>`;
      setTimeout(() => {
        indexPdfBtn.classList.remove("btn-success");
        indexPdfBtn.innerHTML = `<span>Index PDF</span>`;
      }, 4000);

      // 4. Update Sources list with green chunk badge
      const existing = indexedSources.find((s) => s.name === currentFileName);
      if (existing) {
        existing.chunks = data.chunks;
      } else {
        indexedSources.push({ name: currentFileName, chunks: data.chunks });
      }
      renderSources();

      selectedPdfFile = null;
      fileNamePreview.textContent = "";
      pdfFileInput.value = "";
    } catch (err) {
      showToast(err.message, "error");
      indexPdfBtn.innerHTML = `<span>Index PDF</span>`;
    } finally {
      indexPdfBtn.disabled = false;
    }
  });

  // Clear Store Action
  clearStoreBtn.addEventListener("click", async () => {
    if (!confirm("Clear all indexed sources?")) {
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
      if (indexSuccessBanner) indexSuccessBanner.style.display = "none";
      showToast("Sources cleared", "success");
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

    if (emptyState) {
      emptyState.style.display = "none";
    }

    appendMessage("user", query);
    chatInput.value = "";
    chatInput.disabled = true;
    sendBtn.disabled = true;

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
        throw new Error(data.detail || data.message || "Failed to query model");
      }

      appendMessage("assistant", data.answer, data.documents || []);
    } catch (err) {
      removeMessage(pendingId);
      appendMessage("assistant", `Error: ${err.message}`);
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
      header.innerHTML = `<span>Sources (${documents.length})</span><span class="chevron">▾</span>`;
      header.addEventListener("click", () => {
        accordion.classList.toggle("open");
        const chevron = header.querySelector(".chevron");
        if (chevron) {
          chevron.textContent = accordion.classList.contains("open") ? "▴" : "▾";
        }
      });

      const body = document.createElement("div");
      body.className = "sources-accordion-content";
      body.innerHTML = documents
        .map((doc, idx) => {
          const meta = doc.metadata || {};
          const source = meta.source || "Unknown Source";
          const snippet = doc.page_content || "";
          return `
            <div class="source-card">
              <div class="source-card-header">${idx + 1}. ${escapeHtml(source)}</div>
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
    html = html.replace(/`([^`]+)`/g, "<code class='inline-code'>$1</code>");
    // Line breaks to <br>
    html = html.replace(/\n\n/g, "</p><p class='msg-p'>");
    html = html.replace(/\n/g, "<br>");
    return `<p class='msg-p'>${html}</p>`;
  }
});
