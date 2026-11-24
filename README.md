# tool-cat

Bilingual (German/English) **catalogue of generative AI tools for teaching and creating Open Educational Resources**. All content comes from `data/genai_tools.xlsx`, and [Hugo](https://gohugo.io/) renders it as a static website. Every push to `main` deploys the site to GitHub Pages.

## Usage

You only need [uv](https://docs.astral.sh/uv/). It installs Python, the dependencies and Hugo.

```sh
uv sync            # install everything
uv run tcat check  # validate the spreadsheet
uv run tcat serve  # preview at http://localhost:1313/
uv run tcat build  # build the site into site/public/
```

## Suggesting a tool

Know a tool that is missing? [Open an issue](https://github.com/tsmdt/tool-cat/issues/new/choose) with the form in English or German. Every suggestion is reviewed before it is added.

## Funding

`tool-cat` is a project outcome of [AiDaLi: Creating OER to Build AI and Data Literacy](https://transferkiosk.net/p/102025-durch-oer-produktion-zu-ai-und) (2026-2028), funded by [Stiftung Innovation in der Hochschullehre](https://stiftung-hochschullehre.de/en/).

## Acknowledgement

Claude Sonnet 5 and Opus 5 helped to create this app.
