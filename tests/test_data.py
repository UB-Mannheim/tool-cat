import json

import openpyxl
import pytest

from toolcat import data

HEADERS = [
    "title", "type", "description", "url", "notes", "use_cases", "service_location", "costs",
    "is_account_required", "is_opensource", "for_OER_creation", "technical_skill_level",
]
PICKLISTS = [
    ("type_de", "type_en", "use_case_de", "use_case_en", "costs_de", "costs_en", "bool", "technical_skill_level"),
    ("Cloud-Service", "cloud service", "Literaturrecherche", "literature research", "nein", "no", "yes", "low"),
    ("App", "app", "Audiogenerierung (Text-to-Speech)", "audio generation (text-to-speech)",
     "Bezahlversion", "paid", "no", "basic"),
    (None, None, "Chatbot (allgemein)", "chatbot (general)", "Freemium", "freemium", None, None),
]


def tool(**overrides):
    row = {
        "title": "Elicit", "type": "cloud service", "description": "Finds papers.",
        "url": "https://elicit.com/ ", "notes": None, "use_cases": "literature research",
        "service_location": "US", "costs": "freemium", "is_account_required": "yes",
        "is_opensource": "no", "for_OER_creation": "no", "technical_skill_level": "low",
    }
    return row | overrides


@pytest.fixture
def load(tmp_path):
    def _load(*rows, headers=HEADERS):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "tools"
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        pick = wb.create_sheet("picklists")
        for line in PICKLISTS:
            pick.append(line)
        path = tmp_path / "tools.xlsx"
        wb.save(path)
        return data.load(path)

    return _load


def errors(issues):
    return [i.message for i in issues if i.level == "error"]


def test_basic_row(load):
    tools, vocab, issues = load(tool())
    assert not errors(issues)
    assert tools[0] | {"description": None, "notes": None} == {
        "id": "elicit", "title": "Elicit", "url": "https://elicit.com/", "url_is_link": True,
        "type": "cloud service", "use_cases": ["literature research"], "location": "US",
        "location_group": "non_eea", "costs": "freemium", "account": True, "opensource": False,
        "oer": False, "skill": "low", "description": None, "notes": None,
    }
    assert [facet["key"] for facet in vocab] == [
        "type", "use_cases", "location_group", "costs", "account", "opensource", "oer", "skill",
    ]


def test_use_cases_split_with_irregular_spacing(load):
    tools, _, issues = load(tool(use_cases="literature research* chatbot (general) *  * "))
    assert not errors(issues)
    assert tools[0]["use_cases"] == ["literature research", "chatbot (general)"]


def test_use_case_matches_picklist_label_without_parenthetical(load):
    tools, _, issues = load(tool(use_cases="audio generation"))
    assert not errors(issues)
    assert tools[0]["use_cases"] == ["audio generation (text-to-speech)"]


def test_unknown_values_are_errors(load):
    _, _, issues = load(tool(type="website", use_cases="juggling", technical_skill_level="guru"))
    assert len(errors(issues)) == 3
    assert any("website" in message for message in errors(issues))


def test_duplicate_title_is_error(load):
    _, _, issues = load(tool(), tool(title="ELICIT"))
    assert any("duplicate" in message for message in errors(issues))


def test_missing_header_is_error(load):
    _, _, issues = load(tool(), headers=[h for h in HEADERS if h != "costs"])
    assert "costs" in errors(issues)[0]


def test_costs_no_becomes_free(load):
    tools, vocab, issues = load(tool(costs="no"))
    assert not errors(issues)
    assert tools[0]["costs"] == "free"
    costs = next(facet for facet in vocab if facet["key"] == "costs")
    assert costs["values"][0] == {"key": "free", "en": "free", "de": "kostenlos"}


def test_blank_location_is_local_and_eea_is_grouped(load):
    tools, _, _ = load(tool(service_location=None), tool(title="B", service_location="NO"))
    assert (tools[1]["location"], tools[1]["location_group"]) == ("local", "local")
    assert (tools[0]["location"], tools[0]["location_group"]) == ("NO", "eea")


def test_german_falls_back_to_null_and_warns_once(load):
    tools, _, issues = load(tool(), tool(title="B"))
    assert tools[0]["description"] == {"en": "Finds papers.", "de": None}
    assert tools[0]["notes"] == {"en": "", "de": None}
    assert [i.message for i in issues if i.level == "warning"] == ["2 of 2 tools have no description_de"]


def test_german_columns_are_read_when_present(load):
    tools, _, issues = load(tool(description_de="Findet Paper."), headers=HEADERS + ["description_de"])
    assert tools[0]["description"]["de"] == "Findet Paper."
    assert not issues


def test_reordered_columns_and_sorting(load):
    tools, _, issues = load(tool(title="zotero"), tool(title="Asta"), headers=HEADERS[::-1])
    assert not errors(issues)
    assert [t["title"] for t in tools] == ["Asta", "zotero"]


def test_non_link_url_warns(load):
    tools, _, issues = load(tool(url="part of Adobe Acrobat Reader"))
    assert tools[0]["url_is_link"] is False
    assert any("not a link" in i.message for i in issues)


def test_slug_transliterates_umlauts():
    assert data.slugify("Prüf-Öl  (Größe)") == "pruef-oel-groesse"


def test_write(load, tmp_path):
    tools, vocab, _ = load(tool())
    data.write(tools, vocab, tmp_path / "out")
    assert json.loads((tmp_path / "out" / "tools.json").read_text())[0]["id"] == "elicit"
