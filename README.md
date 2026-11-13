# tool-cat

A small bilingual website (English at `/`, German at `/de/`) that presents generative AI tools for teaching and for creating Open Educational Resources. Visitors pick a use case, search, and filter the tool cards.

All content lives in one spreadsheet, `data/genai_tools.xlsx`. A short Python script checks it and turns it into JSON, and [Hugo](https://gohugo.io/) renders the pages. Hugo is installed as a Python package, so [uv](https://docs.astral.sh/uv/) is the only tool you need.

## Quick start

```sh
uv sync                 # install Python packages and Hugo
uv run tool-cat serve   # check the spreadsheet and preview at http://localhost:1313/
```

| Command | What it does |
|---|---|
| `uv run tool-cat check` | Validates the spreadsheet and lists problems. Exits with an error if a row is invalid. |
| `uv run tool-cat serve` | Checks, then starts a live preview. Re-run it after editing the spreadsheet. |
| `uv run tool-cat build [--base-url URL]` | Checks, then writes the finished site to `site/public/`. |
| `uv run pytest` | Runs the tests of the spreadsheet reader. |

## Add or edit a tool

1. Open `data/genai_tools.xlsx` in Excel and add or change a row in the `tools` sheet.
2. Use only values from the `picklists` sheet for `type`, `use_cases`, `costs`, the yes/no columns and `technical_skill_level`. Separate several use cases with `*`, for example `translation * writing assistant`.
3. Leave `service_location` empty for apps that run on the user's own device. Otherwise enter a country code such as `DE` or `US`.
4. Run `uv run tool-cat check`. Fix anything it reports as an error.
5. Commit and push. The site rebuilds itself.

No code change is needed. Two cases need one extra line:

- **A new country code:** add `country_<CODE>` to `site/i18n/en.toml` and `site/i18n/de.toml`. Without it the card shows the bare code.
- **A new use case or type:** add it to the `picklists` sheet first, with its German label next to it. The order of the picklist is the order on the page.

## German texts

Labels for type, use case and costs come from the `*_de` columns of the `picklists` sheet. Everything else in the interface, including the page title (`title`) and the intro text (`intro`), is in `site/i18n/en.toml` and `site/i18n/de.toml`.

Tool descriptions are English until you add these optional columns. Each one is used as soon as it exists; empty cells fall back to English.

| Sheet | Column | Content |
|---|---|---|
| `tools` | `description_de` | German description |
| `tools` | `notes_de` | German note |
| `picklists` | `technical_skill_level_de` | German skill levels, in the same order as `technical_skill_level` |

## Deployment

`.github/workflows/pages.yml` builds and publishes the site to GitHub Pages on every push to `main`. Set it up once: in the repository, open Settings → Pages and choose "GitHub Actions" as the source.

## How it fits together

```
data/genai_tools.xlsx          the only place content is edited
  └─ toolcat/data.py           reads, validates, normalises
       └─ site/data/*.json     generated, not committed
            └─ site/layouts/   Hugo templates render every card and filter as HTML
                 └─ site/assets/   main.css, and app.js for search, filters and the card pile
```

Colours follow the AiDaLi palette in `data/stylesheet/stylesheet.pdf` and are defined once at the top of `site/assets/css/main.css`. Without JavaScript the page lists every tool; the search and filters need it.
