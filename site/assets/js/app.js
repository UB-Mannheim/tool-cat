// tool-cat: search and filter.
// Hugo renders the cards and filter controls; this script only shows and hides them.
function init() {
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
  const norm = (s) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  const search = $("#search"), empty = $("#empty"), panel = $("#filters"), toggle = $("#filter-toggle");
  const app = $("#app"), deck = $("#deck"), browse = $("#browse");
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

  // The page starts closed: the pile beside the title. A click on the pile or on "Filter tools" opens it:
  // the title shrinks into a small header, the filters appear and the cards fly out of the pile into the grid.
  // Every animation moves only transform and opacity, so the browser can run it without re-laying out the page.
  const ease = "cubic-bezier(0.22, 1, 0.36, 1)";
  let opened = false;

  // While closed the pile is one button; the cards inside stay out of the tab order.
  deck.tabIndex = 0;
  deck.setAttribute("role", "button");
  deck.setAttribute("aria-label", deck.dataset.label);
  for (const { el } of cards) el.inert = true;

  function unfold() {
    if (opened) return;
    opened = true;
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const hadFocus = document.activeElement;
    const pile = cards.map(({ el }) => ({ box: el.getBoundingClientRect(), tilt: getComputedStyle(el).rotate }));
    const ghost = still ? null : ghostHero();

    deck.removeAttribute("tabindex");
    deck.removeAttribute("role");
    deck.removeAttribute("aria-label");
    for (const { el } of cards) el.inert = false;
    app.classList.add("open");
    scrollTo(0, 0);
    // The button and the pile are gone now; keep keyboard focus on the page.
    if (hadFocus === browse || hadFocus === deck) $(".goals input").focus({ preventScroll: true });
    if (still) return;
    shrinkHero(ghost);
    fly(pile);
  }

  // A frozen copy of the big title and intro, left where they were, so they can shrink towards the new header.
  function ghostHero() {
    const hero = $(".hero", app), title = $(".site-title", hero), box = hero.getBoundingClientRect();
    const frame = document.createElement("div");
    frame.className = "app ghost"; // keeps the closed-state styles of the copy
    frame.setAttribute("aria-hidden", "true");
    frame.inert = true;
    const copy = hero.cloneNode(true);
    for (const el of [copy, ...copy.querySelectorAll("[id]")]) el.removeAttribute("id");
    frame.append(copy);
    Object.assign(frame.style, {
      position: "fixed", left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`,
      display: "block", minHeight: "0", maxWidth: "none", margin: "0", padding: "0", zIndex: "20", pointerEvents: "none",
    });
    document.body.append(frame);
    return { frame, title: title.getBoundingClientRect(), size: parseFloat(getComputedStyle(title).fontSize), box };
  }

  function shrinkHero({ frame, title: from, size, box }) {
    const title = $(".site-title", app), to = title.getBoundingClientRect();
    const scale = parseFloat(getComputedStyle(title).fontSize) / size;
    frame.style.transformOrigin = `${from.left - box.left}px ${from.top - box.top}px`;
    frame.animate(
      [{ transform: "none", opacity: 1 }, { transform: `translate(${to.left - from.left}px, ${to.top - from.top}px) scale(${scale})`, opacity: 0 }],
      { duration: 480, easing: ease, fill: "forwards" },
    ).finished.then(() => frame.remove(), () => frame.remove());
    for (const el of [title, $(".site-intro", app)]) {
      el.animate([{ opacity: 0 }, { opacity: 0, offset: 0.3 }, { opacity: 1 }], { duration: 520, easing: "ease-out" });
    }
  }

  function fly(pile) {
    cards.forEach(({ el }, i) => {
      const from = pile[i].box, to = el.getBoundingClientRect();
      if (!to.width || to.top > innerHeight * 1.5) return; // hidden or below the fold
      const dx = from.left + from.width / 2 - (to.left + to.width / 2);
      const dy = from.top + from.height / 2 - (to.top + to.height / 2);
      el.animate(
        [{ transform: `translate(${dx}px, ${dy}px) rotate(${pile[i].tilt})` }, { transform: "none" }],
        { duration: 700, delay: Math.min(i, 12) * 22, easing: ease, fill: "backwards" },
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
    timer = setTimeout(update, 100);
  });
  for (const el of $$(".facet")) el.addEventListener("change", update);
  deck.addEventListener("click", unfold);
  deck.addEventListener("keydown", (event) => {
    if (opened || (event.key !== "Enter" && event.key !== " ")) return;
    event.preventDefault();
    unfold();
  });
  browse.addEventListener("click", unfold);
  toggle.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", !panel.hidden);
  });
  for (const button of $$("[data-reset]")) button.addEventListener("click", reset);
  // Escape closes a tooltip opened by keyboard or tap.
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.activeElement?.matches(".hint")) document.activeElement.blur();
  });

  update();
}

init();
