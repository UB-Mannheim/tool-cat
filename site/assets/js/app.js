// tool-cat: search and filter.
// Hugo renders the cards and filter controls; this script only shows and hides them.
function init() {
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
  const norm = (s) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  const search = $("#search"), empty = $("#empty"), panel = $("#filters"), toggle = $("#filter-toggle"), deck = $("#deck");
  const cards = $$(".card").map((el) => ({ el, text: norm(el.dataset.search) }));
  const facets = $$(".facet").map((el) => ({ key: el.dataset.facet, boxes: $$("input", el) }));

  // Within a facet the checked values are ORed; facets and search terms are ANDed.
  function update() {
    const terms = norm(search.value).split(/\s+/).filter(Boolean);
    const picked = facets.map((f) => new Set(f.boxes.filter((b) => b.checked).map((b) => b.value)));
    const tally = facets.map(() => ({}));
    let shown = 0;
    for (const card of cards) {
      const values = facets.map((f) => card.el.dataset[f.key].split("|"));
      const found = terms.every((term) => card.text.includes(term));
      const failed = facets.flatMap((f, i) => (picked[i].size && !values[i].some((v) => picked[i].has(v)) ? [i] : []));
      card.el.hidden = !found || failed.length > 0;
      if (!card.el.hidden) shown++;
      // An option's count is what you would get by ticking it: the card must pass every *other* facet.
      if (!found || failed.length > 1) continue;
      facets.forEach((f, i) => {
        if (failed.length && failed[0] !== i) return;
        for (const v of values[i]) tally[i][v] = (tally[i][v] || 0) + 1;
      });
    }
    facets.forEach((f, i) => f.boxes.forEach((box) => {
      const n = tally[i][box.value] || 0;
      $(".n", box.parentElement).textContent = n;
      box.parentElement.classList.toggle("zero", !n);
    }));
    for (const el of $$("[data-count]")) {
      el.textContent = el.dataset.text.replace("{n}", shown).replace("{total}", cards.length);
    }
    $(".badge", toggle).textContent = $$("input:checked", panel).length || "";
    $("#reset").hidden = !terms.length && !picked.some((set) => set.size);
    empty.hidden = shown > 0;
  }

  // The cards start as a pile. Spread them into the grid, each one flying out from where it lay.
  function unfold() {
    if (deck.classList.contains("open")) return;
    const pile = cards.map(({ el }) => ({ box: el.getBoundingClientRect(), tilt: getComputedStyle(el).rotate }));
    deck.classList.add("open");
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    cards.forEach(({ el }, i) => {
      const from = pile[i].box, to = el.getBoundingClientRect();
      if (!to.width || to.top > innerHeight * 2) return; // hidden or far below the fold
      const dx = from.left + from.width / 2 - (to.left + to.width / 2);
      const dy = from.top + from.height / 2 - (to.top + to.height / 2);
      el.animate(
        [{ transform: `translate(${dx}px, ${dy}px) rotate(${pile[i].tilt})` }, { transform: "none" }],
        { duration: 550, delay: Math.min(i, 16) * 25, easing: "cubic-bezier(0.2, 0.9, 0.25, 1.1)", fill: "backwards" },
      );
    });
  }

  function reset() {
    search.value = "";
    for (const f of facets) for (const box of f.boxes) box.checked = false;
    update();
  }

  let timer;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => (unfold(), update()), 100);
  });
  for (const el of $$(".facet")) el.addEventListener("change", () => (unfold(), update()));
  for (const type of ["pointerenter", "focusin", "click"]) deck.addEventListener(type, unfold);
  toggle.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", !panel.hidden);
  });
  for (const button of $$("[data-reset]")) button.addEventListener("click", reset);

  update();
}

init();
