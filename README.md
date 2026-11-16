# tool-cat

A bilingual website (English and German) that presents generative AI tools for teaching and for creating Open Educational Resources. All content comes from `data/genai_tools.xlsx`, and [Hugo](https://gohugo.io/) renders the site.

## Installation

You only need [uv](https://docs.astral.sh/uv/). It installs Python, the dependencies and Hugo.

```sh
uv sync                 # install everything
uv run tool-cat serve   # preview at http://localhost:1313/
```

or:

```sh
uv run tool-cat build   # build the site into site/public/
```

## Funding

`tool-cat` is a project outcome of [AiDaLi: Promoting AI and Data Literacy Through OER Production](https://transferkiosk.net/p/102025-durch-oer-produktion-zu-ai-und) (2026-2028), funded by [Stiftung Innovation in der Hochschullehre](https://stiftung-hochschullehre.de/en/).

## Acknowledgement

Claude Sonnet 5 and Opus 5 helped to create this app.
