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

const genreChips = document.getElementById("genreChips");
const colorChips = document.getElementById("colorChips");
const grid = document.getElementById("thumbGrid");
const resultCount = document.getElementById("resultCount");
const emptyState = document.getElementById("emptyState");

function renderChips() {
  genreChips.innerHTML = genres
    .map(
      (g) =>
        `<button class="g-chip" data-genre="${g}">${g}</button>`
    )
    .join("");

  colorChips.innerHTML = colors
    .map(
      (c) =>
        `<button class="g-chip" data-color="${c}"><span class="g-chip__swatch bg-${c}"></span>${COLOR_LABELS[c] || c}</button>`
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

function syncChipState() {
  genreChips.querySelectorAll(".g-chip").forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.genre === state.genre);
  });
  colorChips.querySelectorAll(".g-chip").forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.color === state.color);
  });
}

genreChips.addEventListener("click", (e) => {
  const chip = e.target.closest(".g-chip");
  if (!chip) return;
  state.genre = state.genre === chip.dataset.genre ? null : chip.dataset.genre;
  syncChipState();
  renderGrid();
});

colorChips.addEventListener("click", (e) => {
  const chip = e.target.closest(".g-chip");
  if (!chip) return;
  state.color = state.color === chip.dataset.color ? null : chip.dataset.color;
  syncChipState();
  renderGrid();
});

document.getElementById("resetFilters").addEventListener("click", () => {
  state.genre = null;
  state.color = null;
  syncChipState();
  renderGrid();
});

renderChips();
syncChipState();
renderGrid();
