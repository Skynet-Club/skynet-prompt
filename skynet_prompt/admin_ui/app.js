const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const state = {
  items: [],
  categories: [],
  meta: {},
  stats: { count: 0, scenes: 0, official: 0 },
  scene: "all",
  query: "",
  selectedId: null,
  creating: false,
  dirty: false,
  saving: false,
};

const els = {
  sceneList: $("#scene-list"),
  railTotal: $("#rail-total"),
  list: $("#prompt-list"),
  resultLine: $("#result-line"),
  libraryTitle: $("#library-title"),
  search: $("#search"),
  stats: {
    count: $("#stat-count"),
    scenes: $("#stat-scenes"),
    official: $("#stat-official"),
  },
  dataVersion: $("#data-version"),
  dataSha: $("#data-sha"),
  editor: $("#editor"),
  editorEmpty: $("#editor-empty"),
  editorForm: $("#prompt-form"),
  editorMode: $("#editor-mode"),
  editorTitle: $("#editor-title"),
  closeEditor: $("#close-editor"),
  deleteButton: $("#delete-prompt"),
  saveState: $("#save-state"),
  toast: $("#toast"),
  zhCount: $("#zh-count"),
  enCount: $("#en-count"),
};

let toastTimer;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function firstLine(value, max = 94) {
  const text = String(value ?? "").replace(/^#{1,6}\s*/gm, "").replace(/\s+/g, " ").trim();
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}

function sceneLabel(key) {
  const row = state.categories.find(category => category.key === key);
  return row ? row.name : key || "未分类";
}

function categoryFor(key) {
  return state.categories.find(category => category.key === key);
}

function statusFor(item) {
  const verdict = item.evidence?.verdict || "unverified";
  if (verdict === "verbatim") return { css: "verbatim", label: "逐字可核" };
  if (verdict === "paraphrase") return { css: "paraphrase", label: "他人整理" };
  return { css: "unverified", label: "未核实" };
}

function toast(message, error = false) {
  els.toast.textContent = message;
  els.toast.classList.toggle("is-error", error);
  els.toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els.toast.classList.remove("is-visible"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let body = null;
  try { body = await response.json(); } catch {}
  if (!response.ok) throw new Error(body?.error || `HTTP ${response.status}`);
  return body;
}

function setDirty(value) {
  state.dirty = value;
  els.saveState.textContent = value ? "未保存" : "已保存";
  els.saveState.classList.toggle("is-dirty", value);
}

function updateCounts() {
  els.zhCount.textContent = `${els.editorForm.elements.zh.value.length} 字`;
  els.enCount.textContent = `${els.editorForm.elements.en.value.length} 字`;
}

function filteredItems() {
  const needle = state.query.trim().toLowerCase();
  return state.items.filter(item => {
    if (state.scene !== "all" && item.cat !== state.scene) return false;
    if (!needle) return true;
    return [item.zh, item.en, item.author, item.id, sceneLabel(item.cat)]
      .join(" ").toLowerCase().includes(needle);
  });
}

function renderStats() {
  els.stats.count.textContent = state.stats.count;
  els.stats.scenes.textContent = state.stats.scenes;
  els.stats.official.textContent = state.stats.official;
  els.railTotal.textContent = `${state.stats.count} total`;
  els.dataVersion.textContent = state.meta.version || "—";
  const sha = state.meta.sha256 || "";
  els.dataSha.textContent = sha ? `${sha.slice(0, 18)}…` : "—";
  els.dataSha.title = sha;
}

function renderCategoryOptions() {
  $("#field-cat").innerHTML = state.categories
    .map(category => `<option value="${escapeHtml(category.key)}">${escapeHtml(category.name)}</option>`)
    .join("");
}

function renderScenes() {
  const all = state.stats.count;
  const rows = [{ key: "all", name: "全部提示词", count: all }, ...state.categories];
  els.sceneList.innerHTML = rows.map(row => `
    <button class="scene-button${state.scene === row.key ? " is-active" : ""}" type="button"
      data-scene="${escapeHtml(row.key)}">
      <span>${escapeHtml(row.name)}</span>
      <span class="scene-count">${row.count}</span>
    </button>
  `).join("");
}

function renderList() {
  const rows = filteredItems();
  const scene = state.scene === "all" ? "全部提示词" : sceneLabel(state.scene);
  els.libraryTitle.textContent = scene;
  els.resultLine.textContent = state.query
    ? `${rows.length} 条匹配「${state.query}」`
    : `${rows.length} 条提示词 · 点击编辑`;

  if (!rows.length) {
    els.list.innerHTML = `
      <div class="empty-list">
        <strong>没有匹配的提示词</strong>
        清空搜索，或换一个场景。
      </div>`;
    return;
  }

  els.list.innerHTML = rows.map(item => {
    const status = statusFor(item);
    const cat = categoryFor(item.cat);
    const selected = item.id === state.selectedId;
    return `
      <button class="prompt-row${selected ? " is-selected" : ""}" type="button" data-id="${escapeHtml(item.id)}">
        <span class="row-main">
          <span class="row-title">${escapeHtml(firstLine(item.zh))}</span>
          <span class="prompt-en">${escapeHtml(firstLine(item.en, 120))}</span>
          <span class="prompt-meta">
            <span class="scene-tag">${escapeHtml(cat?.name || item.cat)}</span>
            <span class="prompt-id">${escapeHtml(item.id)}</span>
            <span class="prompt-author">${escapeHtml(item.author)}</span>
          </span>
        </span>
        <span class="row-side">
          <span class="status-dot ${status.css}">${status.label}</span>
          <span class="row-arrow">↗</span>
        </span>
      </button>`;
  }).join("");
}

function renderAll() {
  renderStats();
  renderCategoryOptions();
  renderScenes();
  renderList();
}

function formValues() {
  const form = els.editorForm;
  return {
    id: form.elements.id.value.trim(),
    cat: form.elements.cat.value,
    author: form.elements.author.value.trim(),
    date: form.elements.date.value,
    url: form.elements.url.value.trim(),
    zh: form.elements.zh.value.trim(),
    en: form.elements.en.value.trim(),
    nature: form.elements.nature.value,
    excerpt: form.elements.excerpt.checked,
    evidence: { verdict: form.elements.verdict.value },
    source: {
      license: form.elements.license.value.trim() || "not-declared",
      rights_basis: form.elements.rights_basis.value,
      redistribution: form.elements.redistribution.value,
      note: form.elements.note.value.trim(),
    },
  };
}

function resetEditor() {
  state.selectedId = null;
  state.creating = false;
  setDirty(false);
  els.editor.classList.remove("has-selection");
  els.editorForm.hidden = true;
  els.editorEmpty.hidden = false;
  renderList();
}

function closeEditor() {
  if (state.dirty && !confirm("表单还有未保存的修改，确定关闭？")) return;
  resetEditor();
}

function newPrompt() {
  if (state.dirty && !confirm("当前表单还有未保存的修改，确定新建？")) return;
  state.creating = true;
  state.selectedId = null;
  const today = new Date().toISOString().slice(0, 10);
  const stamp = today.replaceAll("-", "");
  const item = {
    id: `custom-${stamp}-${String(state.items.length + 1).padStart(2, "0")}`,
    cat: state.scene === "all" ? "goal" : state.scene,
    author: "",
    date: today,
    url: "",
    zh: "",
    en: "",
    nature: "未核实",
    excerpt: false,
    evidence: { verdict: "unverified" },
    source: {
      license: "not-declared",
      rights_basis: "short-quotation-with-attribution",
      redistribution: "excerpt-only",
      note: "",
    },
  };
  fillEditor(item, true);
  els.editorForm.elements.id.focus();
  els.editorForm.elements.id.select();
}

function fillEditor(item, isNew = false) {
  const form = els.editorForm;
  state.creating = isNew;
  state.selectedId = isNew ? null : item.id;
  form.elements.id.value = item.id || "";
  form.elements.cat.value = item.cat || "goal";
  form.elements.author.value = item.author || "";
  form.elements.date.value = item.date || new Date().toISOString().slice(0, 10);
  form.elements.url.value = item.url || "";
  form.elements.zh.value = item.zh || "";
  form.elements.en.value = item.en || "";
  form.elements.nature.value = item.nature || "未核实";
  form.elements.verdict.value = item.evidence?.verdict || "unverified";
  form.elements.license.value = item.source?.license || "not-declared";
  form.elements.rights_basis.value = item.source?.rights_basis || "short-quotation-with-attribution";
  form.elements.redistribution.value = item.source?.redistribution || "excerpt-only";
  form.elements.note.value = item.source?.note || "";
  form.elements.excerpt.checked = Boolean(item.excerpt);
  els.editorMode.textContent = isNew ? "新建条目" : "编辑条目";
  els.editorTitle.textContent = isNew ? "新提示词" : firstLine(item.zh, 32) || item.id;
  els.deleteButton.disabled = isNew;
  els.deleteButton.title = isNew ? "新建条目保存后才能删除" : "删除条目";
  form.hidden = false;
  els.editorEmpty.hidden = true;
  els.editor.classList.add("has-selection");
  setDirty(false);
  updateCounts();
  renderList();
  requestAnimationFrame(() => {
    const selected = document.querySelector(".prompt-row.is-selected");
    selected?.scrollIntoView({ block: "nearest" });
  });
}

function selectPrompt(id) {
  if (state.selectedId === id && !state.creating) return;
  if (state.dirty && !confirm("当前表单还有未保存的修改，确定切换？")) return;
  const item = state.items.find(row => row.id === id);
  if (!item) return;
  fillEditor(item);
}

function setScene(key) {
  state.scene = key;
  renderScenes();
  renderList();
}

async function load() {
  const data = await api("/api/state");
  state.items = data.items || [];
  state.categories = data.categories || [];
  state.meta = data.meta || {};
  state.stats = data.stats || state.stats;
  renderAll();
}

async function save(event) {
  event.preventDefault();
  if (state.saving) return;
  if (!els.editorForm.reportValidity()) return;
  const values = formValues();
  state.saving = true;
  const button = els.editorForm.querySelector("button[type=submit]");
  button.disabled = true;
  button.textContent = "保存中…";
  try {
    const original = state.selectedId;
    const data = await api(
      original ? `/api/items/${encodeURIComponent(original)}` : "/api/items",
      { method: original ? "PUT" : "POST", body: JSON.stringify(values) },
    );
    state.items = data.state.items;
    state.categories = data.state.categories;
    state.meta = data.state.meta;
    state.stats = data.state.stats;
    state.scene = data.item.cat;
    state.creating = false;
    state.selectedId = data.item.id;
    renderAll();
    fillEditor(data.item);
    setDirty(false);
    toast(`已保存 ${data.item.id} · 备份 ${data.backup}`);
  } catch (error) {
    toast(String(error), true);
  } finally {
    state.saving = false;
    button.disabled = false;
    button.textContent = "保存更改";
  }
}

async function remove() {
  if (state.creating) return;
  const id = state.selectedId;
  if (!id) return;
  if (!confirm(`删除 ${id}？会先写入自动备份。`)) return;
  try {
    const data = await api(`/api/items/${encodeURIComponent(id)}`, { method: "DELETE" });
    state.items = data.state.items;
    state.categories = data.state.categories;
    state.meta = data.state.meta;
    state.stats = data.state.stats;
    resetEditor();
    renderAll();
    toast(`已删除 ${id} · 备份 ${data.backup}`);
  } catch (error) {
    toast(String(error), true);
  }
}

function onFormChange() {
  setDirty(true);
  updateCounts();
}

function bind() {
  $("#new-prompt").addEventListener("click", newPrompt);
  els.closeEditor.addEventListener("click", closeEditor);
  els.deleteButton.addEventListener("click", remove);
  els.editorForm.addEventListener("submit", save);
  els.editorForm.addEventListener("input", onFormChange);
  els.editorForm.addEventListener("change", onFormChange);
  els.search.addEventListener("input", () => {
    state.query = els.search.value;
    renderList();
  });
  els.sceneList.addEventListener("click", event => {
    const button = event.target.closest("[data-scene]");
    if (button) setScene(button.dataset.scene);
  });
  els.list.addEventListener("click", event => {
    const row = event.target.closest("[data-id]");
    if (row) selectPrompt(row.dataset.id);
  });
  window.addEventListener("beforeunload", event => {
    if (!state.dirty) return;
    event.preventDefault();
    event.returnValue = "";
  });
  window.addEventListener("keydown", event => {
    const typing = ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
      if (!els.editorForm.hidden) {
        event.preventDefault();
        els.editorForm.requestSubmit();
      }
      return;
    }
    if (event.key === "/" && !typing) {
      event.preventDefault();
      els.search.focus();
      return;
    }
    if (event.key.toLowerCase() === "n" && !typing && !event.metaKey && !event.ctrlKey) {
      event.preventDefault();
      newPrompt();
      return;
    }
    if (event.key === "Escape") {
      if (!els.editorForm.hidden) closeEditor();
      else if (state.query) {
        els.search.value = "";
        state.query = "";
        renderList();
      }
    }
  });
}

bind();
load().catch(error => toast(`读取失败：${error}`, true));
