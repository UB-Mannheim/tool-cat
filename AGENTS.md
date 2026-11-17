# AGENTS.md

Guidance for coding agents working on `tool-cat`, a bilingual (German/English) static catalogue of generative AI tools for teaching and OER creation.

## How it works

```
data/genai_tools.xlsx ──► toolcat/data.py ──► site/data/{tools,vocab}.json ──► Hugo (site/) ──► site/public/
         (source)          load + validate          (generated, gitignored)        templates        (output)
```

1. `toolcat/data.py` reads two sheets from the workbook:
   - `tools`: one row per tool. Columns are matched by header name, so their order does not matter. Required headers are listed in `REQUIRED`.
   - `picklists`: controlled vocabularies, one column each (`type_en`/`type_de`, `use_case_en`/`use_case_de`, `costs_en`/`costs_de`, `bool`, `technical_skill_level`/`technical_skill_level_de`). Each list ends at its first blank cell.
2. `load()` returns `(tools, vocab, issues)`. Issues are `error` (the build fails) or `warning` (it is only printed).
3. `write()` dumps `tools.json` and `vocab.json` into `site/data/`.
4. Hugo renders every card and filter at build time. `site/assets/js/app.js` only shows and hides them, so the page also works without JavaScript.

## Commands

All tooling runs through [uv](https://docs.astral.sh/uv/). Hugo comes from the `hugo` PyPI package, so don't install it separately.

```sh
uv sync                    # install Python, dependencies and Hugo
uv run tool-cat check      # validate the spreadsheet only
uv run tool-cat serve      # validate, write JSON, run the Hugo dev server on :1313 (binds 0.0.0.0)
uv run tool-cat build      # validate, write JSON, build into site/public/ (--base-url for deploys)
uv run pytest              # run the tests
```

Run `uv run tool-cat check` and `uv run pytest` after changing `toolcat/`.

## Layout

| Path | Purpose |
| --- | --- |
| `data/genai_tools.xlsx` | Source workbook with the `tools` and `picklists` sheets |
| `toolcat/__init__.py` | CLI (`check`, `build`, `serve`) and paths |
| `toolcat/data.py` | Workbook parsing, validation, vocabularies, JSON output |
| `tests/test_data.py` | pytest tests that build small workbooks with openpyxl in `tmp_path` |
| `site/hugo.toml` | Hugo config. German (`de`) is the default language and English is second |
| `site/layouts/` | `baseof.html` (shell, inline SVG icons), `home.html` (page), `_partials/` (card, filters, labels, footer, language switch) |
| `site/i18n/{de,en}.toml` | Interface strings. Spreadsheet labels (type, use case, costs) come from the picklists instead |
| `site/assets/` | `css/main.css`, `js/app.js` (search and filters), `img/` (logos) |
| `.github/workflows/pages.yml` | Builds and deploys to GitHub Pages on push to `main` |

## Conventions and gotchas

- **Data is the source of truth.** Tool content belongs in the spreadsheet. Don't hard-code it in templates or JSON. `site/data/*.json` is generated, so never edit or commit it.
- **The workbook is committed.** The Pages workflow builds from `data/genai_tools.xlsx`, so changes to it are deployed on the next push to `main`. Only `data/stylesheet/stylesheet.pdf` (the palette reference) is gitignored.
- **Keep both languages in sync.** A new interface string goes into both `site/i18n/de.toml` and `site/i18n/en.toml`. Missing German descriptions or notes fall back to English, and the card marks them with `lang="en"`.
- **Facet keys must match across layers.** The vocab keys in `data.py` (`type`, `use_cases`, `location_group`, `costs`, `account`, `opensource`, `oer`, `skill`) appear as `data-*` attributes in `card.html`, as `.facet[data-facet]` in `filters.html`, and in `app.js`. Rename one and you must rename them all.
- **Data rules in `load()`:**
  - Tool `id` is `slugify(title)`, which transliterates umlauts. Duplicate ids are errors.
  - `title`, `type` and `description_en` must be filled in. A blank `description_de` is allowed and only counted in a single warning.
  - `notes_en`/`notes_de` hold one note per line of the cell and become lists. The card shows each note with its own `※`.
  - `use_cases` are separated by `*`. A use case matches a picklist entry with or without its trailing parenthetical.
  - `costs = "no"` becomes `"free"` / `"kostenlos"`.
  - Blank `service_location` means `local`. Codes in `EEA` are grouped as `eea` and all others as `non_eea`.
  - Boolean columns must be `yes`/`no` (taken from the `bool` picklist).
  - Tools are sorted by title, ignoring case.
- **Tests:** the `HEADERS`/`tool()` fixture in `tests/test_data.py` must mirror `REQUIRED` in `data.py`. Update both when you add or rename a column.
- **Filtering logic (`app.js`):** values within one facet are ORed, while facets and search terms are ANDed. An option's count is the number of results you would get by ticking it.
- **Style:** Python ≥ 3.13 with standard library plus `openpyxl` only. Write small functions with short docstrings. Front-end code is vanilla JS and CSS with no build step beyond Hugo's `minify | fingerprint`. Don't add frameworks or new dependencies without asking.
