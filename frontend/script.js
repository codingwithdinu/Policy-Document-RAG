const $ = (selector) => document.querySelector(selector);
const conversation = $("#conversation");
const queryInput = $("#queryInput");
const sendButton = $("#sendButton");
const uploadStatus = $("#uploadStatus");
const fileInput = $("#fileInput");
const dropzone = $("#dropzone");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}
async function readApiResponse(response) {
  const raw = await response.text();
  if (!raw) throw new Error('Server returned an empty response (HTTP ' + response.status + '). Check backend logs and try again.');
  let data;
  try { data = JSON.parse(raw); }
  catch { const preview = raw.replace(/<[^>]*>/g, ' ').replace(/\\s+/g, ' ').trim().slice(0, 180); throw new Error('Server returned non-JSON content (HTTP ' + response.status + '). ' + (preview || 'The API may be unavailable or restarting.')); }
  if (!response.ok) { const detail = typeof data.detail === 'string' ? data.detail : data.message; throw new Error(detail || ('Request failed (HTTP ' + response.status + ').')); }
  return data;
}
function showStatus(message, state = "") {
  uploadStatus.textContent = message;
  uploadStatus.dataset.state = state;
}
function addMessage(role, text, sources = []) {
  const item = document.createElement("article");
  item.className = `message ${role}`;
  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = text;
  item.append(body);
  if (sources.length) {
    const box = document.createElement("div");
    box.className = "sources";
    box.innerHTML = '<div class="sources-title">↳ EVIDENCE RETRIEVED</div>' + sources.map((source, index) =>
      `<div class="source-item"><span>${index + 1}</span><div><b>${escapeHtml(source.source || "Policy document")}</b><small>${source.page ? `Page ${escapeHtml(source.page)}` : "Page not available"} · relevance ${Math.round((source.score || 0) * 100)}%</small></div></div>`
    ).join("");
    item.append(box);
  }
  conversation.append(item);
  conversation.scrollTop = conversation.scrollHeight;
  return item;
}
function setBusy(busy) {
  sendButton.disabled = busy;
  sendButton.textContent = busy ? "…" : "↑";
  queryInput.disabled = busy;
}
async function loadDocuments() {
  try {
    const response = await fetch("/documents");
    const data = await readApiResponse(response);
    $("#docCount").textContent = data.documents.length;
    const list = $("#documentList");
    if (!data.documents.length) {
      list.innerHTML = '<div class="empty-library">No documents yet.<br>Upload one to get started.</div>';
      return;
    }
    list.innerHTML = data.documents.map((doc) => `
      <div class="document-item"><span class="file-icon">▤</span><div class="document-meta"><b title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</b><small>${doc.indexed_chunks} indexed chunks · ${(doc.size_bytes / 1048576).toFixed(1)} MB</small></div><span class="indexed-dot" title="Indexed"></span></div>
    `).join("");
  } catch (error) { console.error(error); }
}
async function uploadFile(file) {
  if (!file) return;
  const extension = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "docx", "txt"].includes(extension)) {
    showStatus("Please choose a PDF, DOCX, or TXT file.", "error"); return;
  }
  if (file.size > 15 * 1048576) {
    showStatus("File is larger than the 15 MB limit.", "error"); return;
  }
  const formData = new FormData();
  formData.append("file", file);
  showStatus(`Uploading and indexing ${file.name}…`, "loading");
  dropzone.classList.add("busy");
  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const result = await readApiResponse(response);
    showStatus(`${result.filename} indexed · ${result.chunks_indexed} chunks ready`, "success");
    addMessage("assistant", `Your document is ready. I indexed ${result.chunks_indexed} text chunks from ${result.filename}. Ask me anything about its policy terms.`);
    await loadDocuments();
  } catch (error) {
    showStatus(error.message || "Could not upload this document.", "error");
  } finally {
    dropzone.classList.remove("busy");
    fileInput.value = "";
  }
}
fileInput.addEventListener("change", () => uploadFile(fileInput.files[0]));
["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
  event.preventDefault(); dropzone.classList.add("drag-over");
}));
["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => {
  event.preventDefault(); dropzone.classList.remove("drag-over");
}));
dropzone.addEventListener("drop", (event) => uploadFile(event.dataTransfer.files[0]));

async function askQuestion(question) {
  const clean = question.trim();
  if (clean.length < 3) return;
  addMessage("user", clean);
  queryInput.value = "";
  setBusy(true);
  const thinking = addMessage("assistant", "Searching your policy and reviewing matching clauses…");
  thinking.classList.add("thinking");
  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: clean })
    });
    const data = await readApiResponse(response);
    thinking.remove();
    addMessage("assistant", data.answer || "No answer was returned.", data.sources || []);
  } catch (error) {
    thinking.remove();
    addMessage("assistant", `I couldn't complete that request: ${error.message}`);
  } finally {
    setBusy(false);
    queryInput.focus();
  }
}
$("#queryForm").addEventListener("submit", (event) => {
  event.preventDefault(); askQuestion(queryInput.value);
});
function bindSuggestions() {
  const node = $("#suggestions");
  if (node) node.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (button) askQuestion(button.textContent);
  });
}
bindSuggestions();
$("#clearChat").addEventListener("click", () => {
  conversation.innerHTML = '<div class="welcome-block"><div class="welcome-spark">✳</div><span class="section-kicker">YOUR POLICY, DECODED</span><h3>What would you like<br>to understand?</h3><p>Ask about coverage, exclusions, waiting periods, claim conditions, and more.</p></div><div class="suggestions" id="suggestions"><button class="suggestion">Is hospitalisation covered?</button><button class="suggestion">What are the waiting periods?</button><button class="suggestion">Which treatments are excluded?</button></div>';
  bindSuggestions();
});
queryInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault(); $("#queryForm").requestSubmit();
  }
});
loadDocuments();
