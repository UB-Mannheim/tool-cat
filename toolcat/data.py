import json
import re
import unicodedata
import warnings
from dataclasses import dataclass
from pathlib import Path

import openpyxl

REQUIRED = [
    "title", "type", "description_de", "description_en", "url", "notes_de", "notes_en", "use_cases",
    "service_location", "costs", "is_account_required", "is_opensource", "for_OER_creation",
    "technical_skill_level",
]
BOOLS = {"account": "is_account_required", "opensource": "is_opensource", "oer": "for_OER_creation"}
EEA = [
    "EU", "DE", "AT", "FR", "NL", "BE", "LU", "IT", "ES", "PT", "IE", "DK", "SE", "FI", "PL",
    "CZ", "SK", "SI", "HR", "HU", "RO", "BG", "GR", "CY", "MT", "EE", "LV", "LT", "NO", "IS", "LI"
]
UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})


@dataclass
class Issue:
    level: str  # "error" | "warning"
    row: int | None
    message: str

    def __str__(self):
        where = f"row {self.row}: " if self.row else ""
        return f"{self.level.upper()}: {where}{self.message}"


def slugify(text):
    text = unicodedata.normalize("NFKD", text.translate(UMLAUTS)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _rows(ws):
    """
    Yield (row_number, {header: stripped string}) for every non-empty row below the header.
    """
    rows = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows, [])]
    for number, row in enumerate(rows, start=2):
        cells = ["" if c is None else str(c).strip() for c in row]
        if any(cells):
            test = number, {h: c for h, c in zip(headers, cells) if h}
            yield test


def _picklists(ws):
    """
    Return {column: [values]} with each list ending at its first blank cell.
    """
    lists, done = {}, set()
    for _, row in _rows(ws):
        for header, value in row.items():
            if not value:
                done.add(header)
            elif header not in done:
                lists.setdefault(header, []).append(value)
    return lists


def _pairs(lists, name):
    """Pair the `<name>_en` and `<name>_de` picklist columns into vocab values."""
    en, de = lists.get(f"{name}_en", []), lists.get(f"{name}_de", [])
    return [{"key": e, "en": e, "de": de[i] if i < len(de) else e} for i, e in enumerate(en)]


def _vocab(lists):
    """
    Return controlled vocabularies from the .xslx
    """
    # Costs
    costs = _pairs(lists, "costs")
    for value in costs:
        if value["key"] == "no":
            value.update(key="free", en="free", de="kostenlos")

    # Technical skills
    skill_de = lists.get("technical_skill_level_de", [])
    skills = []
    for i, key in enumerate(lists.get("technical_skill_level", [])):
        value = {"key": key, "en": key}
        if i < len(skill_de):  # otherwise Hugo falls back to the i18n key skill_<value>
            value["de"] = skill_de[i]
        skills.append(value)

    # Bool vocab
    yes_no = [{"key": "true"}, {"key": "false"}]  # labels come from the i18n files

    return [
        {"key": "type", "values": _pairs(lists, "type")},
        {"key": "use_cases", "values": _pairs(lists, "use_case")},
        {"key": "location_group", "values": [{"key": "local"}, {"key": "eea"}, {"key": "non_eea"}]},
        {"key": "costs", "values": costs},
        *({"key": key, "values": yes_no} for key in BOOLS),
        {"key": "skill", "values": skills},
    ]


def load(xlsx_path):
    """
    Return (tools, vocab, issues) for the workbook at `xlsx_path`.
    """
    def pick(column, facet, value=None):
        value = row[column] if value is None else value
        if value not in allowed[facet]:
            error(number, f"{column} '{row[column]}' is not in the picklists")
        return value

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        picklists = _picklists(wb["picklists"])
        rows = list(_rows(wb["tools"]))

    issues = []
    error = lambda row, message: issues.append(Issue("error", row, message))

    vocab = _vocab(picklists)
    allowed = {facet["key"]: [v["key"] for v in facet["values"]] for facet in vocab}
    use_cases = {re.sub(r"\s*\([^)]*\)$", "", key): key for key in allowed["use_cases"]}
    use_cases.update({key: key for key in allowed["use_cases"]})
    bools = {v: v == "yes" for v in picklists.get("bool", ["yes", "no"])}

    missing = [h for h in REQUIRED if not rows or h not in rows[0][1]]
    if missing:
        error(None, f"missing required column(s) in sheet 'tools': {', '.join(missing)}")
        return [], vocab, issues

    tools, seen = [], {}
    missing_en_desc = missing_de_desc = 0
    for number, row in rows:
        for field in ("title", "type", "description_de", "description_en"):
            if not row[field]:
                error(number, f"missing {field}")

        tool_id = slugify(row["title"])
        if tool_id and tool_id in seen:
            error(number, f"duplicate tool '{row['title']}' (same id as row {seen[tool_id]})")
        seen.setdefault(tool_id, number)

        cases = []
        for part in filter(None, (p.strip() for p in row["use_cases"].split("*"))):
            if part in use_cases:
                cases.append(use_cases[part])
            else:
                error(number, f"use case '{part}' is not in the picklists")

        flags = {}
        for key, column in BOOLS.items():
            if row[column] not in bools:
                error(number, f"{column} '{row[column]}' must be yes or no")
            flags[key] = bools.get(row[column], False)

        url, location = row["url"], row["service_location"].upper()
        if not url.startswith("http"):
            issues.append(Issue("warning", number, f"url of '{row['title']}' is not a link: '{url}'"))

        missing_en_desc += not row.get("description_en")
        missing_de_desc += not row.get("description_de")
        tools.append({
            "id": tool_id,
            "title": row["title"],
            "url": url,
            "url_is_link": url.startswith("http"),
            "type": pick("type", "type"),
            "use_cases": cases,
            "location": location or "local",
            "location_group": "local" if not location else "eea" if location in EEA else "non_eea",
            "costs": pick("costs", "costs", "free" if row["costs"] == "no" else row["costs"]),
            **flags, "skill": pick("technical_skill_level", "skill"),
            "description": {
                "en": row.get("description_en") or None,
                "de": row.get("description_de") or None
            },
            "notes": {"en": row.get("notes_en") or None, "de": row.get("notes_de") or None}
        })

    if missing_en_desc > 0 or missing_de_desc > 0:
        issues.append(Issue(
            "warning", None, (
                f"{missing_en_desc} of {len(tools)} tools have no description_en and "
                f"{missing_de_desc} of {len(tools)} tools have no description_de "
            )
        ))

    tools.sort(key=lambda tool: tool["title"].casefold())

    return tools, vocab, issues


def write(tools, vocab, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in (("tools.json", tools), ("vocab.json", vocab)):
        (out_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
