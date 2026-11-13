"""tool-cat: build the GenAI tool catalogue from data/genai_tools.xlsx."""

import argparse
import subprocess
import sys
from pathlib import Path

from . import data

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "data" / "genai_tools.xlsx"
SITE = ROOT / "site"


def check():
    """Load and validate the workbook, print the issues, exit 1 on errors."""
    tools, vocab, issues = data.load(XLSX)
    for issue in issues:
        print(issue, file=sys.stderr)
    errors = sum(issue.level == "error" for issue in issues)
    print(f"{len(tools)} tools, {errors} errors, {len(issues) - errors} warnings")
    if errors:
        sys.exit(1)
    return tools, vocab


def main():
    parser = argparse.ArgumentParser(prog="tool-cat", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate the spreadsheet")
    build = commands.add_parser("build", help="validate, write JSON and build the site")
    build.add_argument("--base-url", help="public URL of the site, e.g. https://example.github.io/tool-cat/")
    commands.add_parser("serve", help="validate, write JSON and start the Hugo dev server")
    args = parser.parse_args()

    tools, vocab = check()
    if args.command == "check":
        return
    data.write(tools, vocab, SITE / "data")
    if args.command == "build":
        base = ["--baseURL", args.base_url] if args.base_url else []
        subprocess.run(["hugo", "--minify", "-s", str(SITE), *base], check=True)
    else:
        subprocess.run(["hugo", "server", "-s", str(SITE), "--bind", "0.0.0.0"], check=True)
