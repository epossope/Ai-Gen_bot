const API_BASE = window.location.origin;

const state = {
  userId: 1,
  username: null,
  schema: { sections: [], modelCards: [] },
  activeTab: "models",
  activeSection: "generation",
};

const el = {
  tabs: document.getElementById("tabs"),
  subtabs: document.getElementById("subtabs"),
  modelsList: document.getElementById("modelsList"),
  historyList: document.getElementById("historyList"),
  modelSelect: document.getElementById("modelSelect"),
  modeSelect: document.getElementById("modeSelect"),
  promptInput: document.getElementById("promptInput"),
  form: document.getElementById("generateForm"),
  resultBox: document.getElementById("resultBox"),
  balanceValue: document.getElementById("balanceValue"),
  cabinetUser: document.getElementById("cabinetUser"),
  panels: {
    models: document.getElementById("modelsPanel"),
    history: document.getElementById("historyPanel"),
    cabinet: document.getElementById("cabinetPanel"),
  },
};

function getTelegramUser() {
  try {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      const user = window.Telegram.WebApp.initDataUnsafe?.user;
      if (user?.id) {
        return { id: Number(user.id), username: user.username || null };
      }
    }
  } catch (error) {
    console.warn("Telegram init error", error);
  }
  return { id: Number(localStorage.getItem("demo_user_id") || 1), username: "demo_user" };
}

async function post(path, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = body.detail || `Request failed: ${res.status}`;
    throw new Error(msg);
  }
  return body;
}

async function get(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function renderTabs() {
  el.tabs.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === state.activeTab);
    btn.onclick = () => {
      state.activeTab = btn.dataset.tab;
      for (const [key, panel] of Object.entries(el.panels)) {
        panel.classList.toggle("hidden", key !== state.activeTab);
      }
      renderTabs();
    };
  });
}

function cardsBySection(sectionId) {
  return state.schema.modelCards.filter((m) => m.section === sectionId);
}

function renderSubtabs() {
  el.subtabs.innerHTML = "";
  for (const section of state.schema.sections) {
    const btn = document.createElement("button");
    btn.className = `subtab ${state.activeSection === section.id ? "active" : ""}`;
    btn.textContent = section.title;
    btn.onclick = () => {
      state.activeSection = section.id;
      renderSubtabs();
      renderModels();
    };
    el.subtabs.appendChild(btn);
  }
}

function renderModels() {
  const cards = cardsBySection(state.activeSection);
  el.modelsList.innerHTML = "";
  for (const card of cards) {
    const wrapper = document.createElement("article");
    wrapper.className = "card";
    wrapper.innerHTML = `
      <div class="card-top">
        <h3>${card.title}</h3>
        <span class="price">${card.price} tokens</span>
      </div>
      <p class="muted">${card.description}</p>
      <p class="muted">id: ${card.id}</p>
    `;
    el.modelsList.appendChild(wrapper);
  }
}

function renderModelSelect() {
  el.modelSelect.innerHTML = "";
  for (const card of state.schema.modelCards) {
    const option = document.createElement("option");
    option.value = card.id;
    option.textContent = `${card.title} (${card.price} tokens)`;
    el.modelSelect.appendChild(option);
  }
}

async function refreshProfile() {
  const profile = await post("/miniapp/profile", {
    tg_user_id: state.userId,
    username: state.username,
  });
  el.balanceValue.textContent = profile.balance;
  el.cabinetUser.textContent = `User: ${profile.username || "no_username"} | id: ${profile.telegramId}`;
}

async function refreshHistory() {
  const history = await post("/miniapp/history", { tg_user_id: state.userId });
  el.historyList.innerHTML = "";
  const items = history.items || [];
  if (!items.length) {
    el.historyList.innerHTML = `<div class="card"><p class="muted">No demo runs yet.</p></div>`;
    return;
  }
  for (const item of items) {
    const article = document.createElement("article");
    article.className = "card";
    article.innerHTML = `
      <div class="card-top">
        <h3>${item.modelTitle}</h3>
        <span class="price">${item.price} tokens</span>
      </div>
      <p class="muted">${item.mode} | ${new Date(item.createdAt).toLocaleString()}</p>
      <p class="muted">${item.prompt}</p>
      <img src="${item.imageUrl}" alt="history image"/>
    `;
    el.historyList.appendChild(article);
  }
}

async function loadSchema() {
  state.schema = await get("/schema");
  renderSubtabs();
  renderModels();
  renderModelSelect();
}

function wireForm() {
  el.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const modelId = el.modelSelect.value;
    const mode = el.modeSelect.value;
    const prompt = el.promptInput.value.trim();
    el.resultBox.innerHTML = `<p class="muted">Running demo request...</p>`;
    try {
      const result = await post("/miniapp/generate", {
        tg_user_id: state.userId,
        username: state.username,
        model_id: modelId,
        mode,
        prompt,
      });
      el.resultBox.innerHTML = `
        <img src="${result.imageUrl}" alt="result"/>
        <div class="result-meta">
          <div>Model: ${result.modelTitle}</div>
          <div>Prompt: ${result.prompt}</div>
          <div>Spent: ${result.price} tokens</div>
          <div>Balance: ${result.balance} tokens</div>
        </div>
      `;
      await refreshProfile();
      await refreshHistory();
    } catch (error) {
      el.resultBox.innerHTML = `<p class="muted">Error: ${error.message}</p>`;
    }
  });
}

async function boot() {
  const tg = getTelegramUser();
  state.userId = tg.id;
  state.username = tg.username;
  renderTabs();
  wireForm();
  await loadSchema();
  await refreshProfile();
  await refreshHistory();
}

boot().catch((error) => {
  console.error(error);
  el.resultBox.innerHTML = `<p class="muted">Startup error: ${error.message}</p>`;
});
