import json
import re

from teamkb.bundle import publishable
from teamkb.cards import CONTROL_CHARS, load_cards
from teamkb.config import load_config

from .conftest import EXAMPLE, REPO

TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".toml"}


def test_agent_instructions_fit_the_limit():
    # Declarative agent manifest 1.8: instructions are 8,000 characters or less.
    text = (REPO / "copilot" / "agent" / "instructions.txt").read_text(encoding="utf-8")
    assert 0 < len(text) <= 8000


def test_manifest_points_to_instructions_and_published_folder():
    manifest = json.loads((REPO / "copilot" / "agent" / "declarativeAgent.json").read_text())
    assert manifest["version"] == "v1.8"
    assert manifest["instructions"] == "$[file('instructions.txt')]"
    assert len(manifest["name"]) <= 100 and len(manifest["description"]) <= 1000
    urls = [i["url"] for c in manifest["capabilities"] for i in c.get("items_by_url", [])]
    assert urls and all(u.endswith("/_published") for u in urls)
    assert len(manifest["conversation_starters"]) <= 12


def test_prompts_ask_for_a_read_check():
    for name in ("ask.txt", "curate.txt"):
        text = (REPO / "copilot" / "prompt-only" / name).read_text(encoding="utf-8")
        assert 'Start your reply with one line: "Read:' in text
        assert re.search(r"never (as )?instructions", text)


def test_curate_prompt_template_matches_card_fields():
    text = (REPO / "copilot" / "prompt-only" / "curate.txt").read_text(encoding="utf-8")
    for field in (
        "id:",
        "type:",
        "title:",
        "status: draft",
        "classification:",
        "owner:",
        "tags:",
        "sources:",
        "verified:",
        "review_by:",
        "related:",
        "supersedes:",
        "superseded_by:",
        "created:",
        "updated:",
        "## Summary",
    ):
        assert field in text, field


def test_no_control_characters_anywhere_in_the_repository():
    skip = {".git", ".venv", ".ruff_cache", ".pytest_cache"}
    offenders = [
        str(path.relative_to(REPO))
        for path in REPO.rglob("*")
        if path.is_file()
        and path.suffix in TEXT_SUFFIXES
        and not skip & set(path.parts)
        and CONTROL_CHARS.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_eval_questions_match_the_example():
    config = load_config(EXAMPLE)
    cards, _ = load_cards(config.cards_path)
    published = {c.id for c in publishable(config, cards)[0]}
    all_ids = {c.id for c in cards}
    lines = (REPO / "evals" / "questions.jsonl").read_text(encoding="utf-8").splitlines()
    questions = [json.loads(line) for line in lines if line.strip()]
    assert len({q["id"] for q in questions}) == len(questions)
    for q in questions:
        assert set(q["expected_cards"]) <= published, q["id"]
        assert set(q["must_not_use"]) <= all_ids, q["id"]
        assert not set(q["must_not_use"]) & set(q["expected_cards"]), q["id"]
    kinds = {q["kind"] for q in questions}
    assert {"draft-only", "above-ceiling", "injection"} <= kinds


def test_example_has_no_real_looking_contact_details():
    text = "\n".join(p.read_text(encoding="utf-8") for p in EXAMPLE.rglob("*.md"))
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
