const state = {
  categories: [],
  items: [],
  current: null,
  category: "",
  selected: new Map(),
  timer: null,
};

const el = {
  status: document.querySelector("#status"),
  search: document.querySelector("#search"),
  categories: document.querySelector("#categories"),
  count: document.querySelector("#count"),
  items: document.querySelector("#items"),
  emptyDetail: document.querySelector("#empty-detail"),
  detail: document.querySelector("#detail"),
  detailCategory: document.querySelector("#detail-category"),
  detailTitle: document.querySelector("#detail-title"),
  evidence: document.querySelector("#evidence"),
  insertText: document.querySelector("#insert-text"),
  add: document.querySelector("#add"),
  author: document.querySelector("#author"),
  date: document.querySelector("#date"),
  nature: document.querySelector("#nature"),
  checked: document.querySelector("#checked"),
  sourceQuote: document.querySelector("#source-quote"),
  sourceLink: document.querySelector("#source-link"),
  selected: document.querySelector("#selected"),
  composed: document.querySelector("#composed"),
  copy: document.querySelector("#copy"),
  clear: document.querySelector("#clear"),
};

const evidenceNames = {
  verbatim: "逐字可核",
  paraphrase: "他人整理",
  unverified: "未核实",
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
}

function categoryName(key) {
  return state.categories.find((row) => row.key === key)?.name || key;
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}

function renderCategories() {
  el.categories.replaceChildren();
  const rows = [{ key: "", name: "全部", count: state.categories.reduce((n, row) => n + row.count, 0) }];
  rows.push(...state.categories.filter((row) => row.count > 0));
  for (const row of rows) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category";
    button.classList.toggle("active", state.category === row.key);
    const name = document.createElement("span");
    name.textContent = row.name;
    const count = document.createElement("small");
    count.textContent = row.count;
    button.append(name, count);
    button.addEventListener("click", () => {
      state.category = row.key;
      renderCategories();
      loadItems();
    });
    el.categories.append(button);
  }
}

function renderItems() {
  el.count.textContent = `${state.items.length} 条`;
  el.items.replaceChildren();
  if (!state.items.length) {
    const empty = document.createElement("p");
    empty.className = "quote";
    empty.textContent = "没有匹配的提示词。";
    el.items.append(empty);
    return;
  }
  for (const item of state.items) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "item-card";
    button.classList.toggle("active", state.current?.id === item.id);
    const title = document.createElement("strong");
    title.textContent = item.zh;
    const meta = document.createElement("span");
    meta.textContent = `${categoryName(item.cat)} · ${item.author}`;
    button.append(title, meta);
    button.addEventListener("click", () => selectItem(item));
    el.items.append(button);
  }
}

function selectItem(item) {
  state.current = item;
  renderItems();
  el.emptyDetail.hidden = true;
  el.detail.hidden = false;
  el.detailCategory.textContent = categoryName(item.cat);
  el.detailTitle.textContent = item.zh;
  el.insertText.textContent = item.zh;
  const verdict = item.evidence?.verdict || "unverified";
  el.evidence.textContent = evidenceNames[verdict] || verdict;
  el.evidence.className = `badge ${verdict}`;
  el.author.textContent = item.author;
  el.date.textContent = item.date;
  el.nature.textContent = item.nature || "未标注";
  el.checked.textContent = item.evidence?.checked_at || "未核对";
  el.sourceQuote.textContent = item.source?.quote || item.en;
  el.sourceLink.href = safeUrl(item.source?.url || item.url);
  el.add.disabled = state.selected.has(item.id);
  el.add.textContent = state.selected.has(item.id) ? "已加入" : "加入组合";
}

function renderSelected() {
  el.selected.replaceChildren();
  for (const [id, item] of state.selected) {
    const chip = document.createElement("span");
    chip.className = "chip";
    const text = document.createElement("span");
    text.textContent = item.zh;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.title = "移除";
    remove.textContent = "×";
    remove.addEventListener("click", () => {
      state.selected.delete(id);
      renderSelected();
      if (state.current?.id === id) selectItem(state.current);
    });
    chip.append(text, remove);
    el.selected.append(chip);
  }
  if (state.current) selectItem(state.current);
}

async function renderComposition() {
  const ids = [...state.selected.keys()];
  el.copy.disabled = ids.length === 0;
  if (!ids.length) {
    el.composed.value = "";
    return;
  }
  const result = await api("/v1/compose", {
    method: "POST",
    body: JSON.stringify({ ids, field: "zh" }),
  });
  el.composed.value = result.text;
}

async function loadItems() {
  try {
    state.items = await api("/v1/search", {
      method: "POST",
      body: JSON.stringify({
        query: el.search.value.trim(),
        category: state.category || undefined,
      }),
    });
    if (state.current && !state.items.some((item) => item.id === state.current.id)) {
      state.current = null;
      el.detail.hidden = true;
      el.emptyDetail.hidden = false;
    }
    renderItems();
  } catch (error) {
    el.status.textContent = `搜索失败：${error.message}`;
  }
}

async function init() {
  try {
    const [packs, categories] = await Promise.all([
      api("/v1/packs"),
      api("/v1/categories"),
    ]);
    state.categories = categories;
    const count = packs.reduce((sum, pack) => sum + pack.count, 0);
    el.status.textContent = `${packs.length} 个包 · ${count} 条 · 本地只读`;
    renderCategories();
    await loadItems();
  } catch (error) {
    el.status.textContent = `加载失败：${error.message}`;
  }
}

el.search.addEventListener("input", () => {
  clearTimeout(state.timer);
  state.timer = setTimeout(loadItems, 180);
});

el.add.addEventListener("click", async () => {
  if (!state.current) return;
  state.selected.set(state.current.id, state.current);
  renderSelected();
  await renderComposition();
});

el.clear.addEventListener("click", async () => {
  state.selected.clear();
  renderSelected();
  await renderComposition();
});

el.copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(el.composed.value);
    el.status.textContent = "已复制组合文本";
  } catch {
    el.composed.focus();
    el.composed.select();
    el.status.textContent = "请按系统复制快捷键";
  }
});

init();
