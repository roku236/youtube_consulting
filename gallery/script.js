const COLOR_LABELS = {
  red: "レッド",
  blue: "ブルー",
  yellow: "イエロー",
  green: "グリーン",
  purple: "パープル",
  pink: "ピンク",
  orange: "オレンジ",
  black: "ブラック",
};

const state = { genre: null, color: null };

const genres = [...new Set(THUMBNAILS.map((t) => t.genre))];
const colors = [...new Set(THUMBNAILS.map((t) => t.color))];

const genreList = document.getElementById("genreList");
const colorList = document.getElementById("colorList");
const grid = document.getElementById("thumbGrid");
const resultCount = document.getElementById("resultCount");
const emptyState = document.getElementById("emptyState");

function renderLists() {
  genreList.innerHTML = genres
    .map((g) => `<li><button data-genre="${g}">${g}</button></li>`)
    .join("");

  colorList.innerHTML = colors
    .map(
      (c) =>
        `<li><button data-color="${c}"><span class="g-swatch bg-${c}"></span>${COLOR_LABELS[c] || c}</button></li>`
    )
    .join("");
}

function renderGrid() {
  const filtered = THUMBNAILS.filter((t) => {
    if (state.genre && t.genre !== state.genre) return false;
    if (state.color && t.color !== state.color) return false;
    return true;
  });

  resultCount.textContent = `${filtered.length}件`;
  emptyState.hidden = filtered.length > 0;

  grid.innerHTML = filtered
    .map(
      (t) => `
      <a class="g-card" href="${t.url}" target="_blank" rel="noopener">
        <div class="g-card__thumb bg-${t.color}">
          <span class="g-card__genre-tag">${t.genre}</span>
          <div class="g-card__title">${t.title}</div>
        </div>
        <div class="g-card__meta">
          <div class="g-card__channel">${t.channel}</div>
          <div class="g-card__views">再生回数 ${t.views}回</div>
        </div>
      </a>`
    )
    .join("");
}

function syncListState() {
  genreList.querySelectorAll("button").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.genre === state.genre);
  });
  colorList.querySelectorAll("button").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.color === state.color);
  });
}

genreList.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  state.genre = state.genre === btn.dataset.genre ? null : btn.dataset.genre;
  syncListState();
  renderGrid();
});

colorList.addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  state.color = state.color === btn.dataset.color ? null : btn.dataset.color;
  syncListState();
  renderGrid();
});

document.getElementById("resetFilters").addEventListener("click", () => {
  state.genre = null;
  state.color = null;
  syncListState();
  renderGrid();
});

renderLists();
syncListState();
renderGrid();
