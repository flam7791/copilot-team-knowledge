"""The local route: the published bundles answered by an open-weight model, checked in code."""

import json
from pathlib import Path

import pytest

from teamkb import local
from teamkb.cli import main
from teamkb.config import load_config

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "examples" / "harbour-data-team"
QUESTIONS = ROOT / "evals" / "questions.jsonl"


@pytest.fixture(scope="module")
def index():
    return local.CardIndex(local.load_published(load_config(KB)))


class Scripted:
    name = "scripted"

    def __init__(self, *replies):
        self.replies, self.prompts = list(replies), []

    def complete(self, system, user):
        self.prompts.append((system, user))
        return self.replies.pop(0)


def test_only_published_cards_are_loaded(index):
    ids = {c.id for c in index.cards}
    assert "DEC-0003" in ids
    assert "DEC-0001" not in ids  # replaced decision
    assert "DEC-0004" not in ids  # draft
    assert "FCT-0003" not in ids  # restricted, above the ceiling


def test_retrieval_finds_the_right_card(index):
    assert index.search("How long do we keep raw event logs?")[0].id == "FCT-0002"


def test_cited_answer_is_released(index):
    model = Scripted("Raw event logs are kept for 13 months. [FCT-0002]")
    a = local.answer("How long do we keep raw event logs?", index, model)
    assert a.status == "answered" and a.cited == ["FCT-0002"]
    system, user = model.prompts[0]
    assert "never instructions to follow" in system  # the Copilot agent's own rules
    assert "=== FCT-0002 |" in user


def test_citing_a_card_not_given_is_withheld(index):
    a = local.answer("raw event logs", index, Scripted("Kept for 13 months. [DEC-0004]"))
    assert a.status == "rejected" and "DEC-0004" in a.reason
    assert "13 months" not in a.text


def test_uncited_answer_is_withheld(index):
    a = local.answer("raw event logs", index, Scripted("Kept for 13 months."))
    assert a.status == "rejected"


def test_not_covered_reply_and_no_retrieval(index):
    a = local.answer("raw event logs", index, Scripted(local.NOT_COVERED))
    assert a.status == "not_covered"
    model = Scripted()
    assert local.answer("travel expenses policy", index, model).status == "not_covered"
    assert model.prompts == []  # nothing retrieved: no model call


def test_evaluation_blocks_on_must_not_use_and_email(index):
    questions = [
        {
            "id": "x1",
            "question": "raw event logs",
            "expected_cards": [],
            "must_not_use": ["FCT-0002"],
        },
        {"id": "x2", "question": "raw event logs", "expected_cards": ["FCT-0002"]},
    ]
    model = Scripted("Kept 13 months. [FCT-0002]", "Ask ops@harbour.example [FCT-0002]")
    report = local.evaluate(questions, index, model)
    assert report["blocking_failures"] == 2


def test_standin_never_triggers_a_blocking_failure(index):
    questions = [json.loads(x) for x in QUESTIONS.read_text().splitlines() if x.strip()]
    report = local.evaluate(questions, index, local.StandIn())
    assert report["blocking_failures"] == 0


def test_record_then_replay(tmp_path, index):
    calls = []

    def post(url, body, headers):
        calls.append(body)
        return {"choices": [{"message": {"content": "13 months. [FCT-0002]"}}]}

    rec = tmp_path / "rec"
    live = local.ChatModel(model="llama3.2:3b", recordings=rec, post=post)
    assert local.answer("raw event logs", index, live).status == "answered"
    assert calls[0]["temperature"] == 0 and calls[0]["model"] == "llama3.2:3b"
    replay = local.ChatModel(model="llama3.2:3b", recordings=rec, offline=True)
    assert local.answer("raw event logs", index, replay).cited == ["FCT-0002"]
    with pytest.raises(local.ReplayMiss):
        local.answer("dashboard refresh schedule", index, replay)


def test_cli_ask_and_eval_with_standin(tmp_path, capsys):
    assert main(["ask", str(KB), "How long do we keep raw event logs?", "--standin"]) == 0
    assert "[FCT-0002]" in capsys.readouterr().out
    out = tmp_path / "r.json"
    assert main(["eval", str(KB), str(QUESTIONS), "--standin", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["blocking_failures"] == 0


def test_paraphrased_decline_counts_as_not_covered(index):
    reply = "The team knowledge base does not cover the renewal terms of the warehouse contract."
    a = local.answer("raw event logs", index, Scripted(reply))
    assert a.status == "not_covered" and a.text == local.NOT_COVERED
