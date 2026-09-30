import pytest

from teamkb.config import load_config
from teamkb.validate import validate

from .conftest import TODAY, card_path, edit


def codes(config, level="error"):
    report = validate(config, TODAY)
    return {i.code for i in report.issues if i.level == level}


def test_example_is_clean(config):
    report = validate(config, TODAY)
    assert report.ok, [str(i) for i in report.issues]
    assert report.warnings == []
    assert len(report.cards) == 12


def test_control_character_is_an_error(kb, config):
    # The failure this rule exists for: a generator writes "`b" or "`0" inside a string and
    # the file silently gains a backspace or a null character.
    edit(kb, "DEC-0002", "The team reviews", "The team \x08reviews")
    assert "control-char" in codes(config)


def test_zero_width_character_is_an_error(kb, config):
    edit(kb, "DEC-0002", "cloud spend", "cloud\u200b spend")
    assert "control-char" in codes(config)


def test_missing_required_field(kb, config):
    edit(kb, "DEC-0002", "owner: Data platform lead\n", "")
    assert "missing-field" in codes(config)


def test_id_must_match_type(kb, config):
    path = edit(kb, "DEC-0002", "id: DEC-0002", "id: FCT-0009")
    path.rename(path.with_name("FCT-0009 - Review cloud costs every month.md"))
    assert "id-type-mismatch" in codes(config)


def test_card_must_be_in_its_type_folder(kb, config):
    path = card_path(kb, "TRM-0001")
    path.rename(kb / "cards" / "facts" / path.name)
    assert "wrong-folder" in codes(config)


def test_filename_must_match_id_and_title(kb, config):
    edit(kb, "DEC-0002", "title: Review cloud costs every month", "title: Review costs monthly")
    assert "filename" in codes(config)


def test_forbidden_title_characters(kb, config):
    edit(kb, "DEC-0002", "title: Review cloud costs every month", 'title: "Review costs: monthly?"')
    assert "title-chars" in codes(config)


def test_duplicate_id(kb, config):
    src = card_path(kb, "DEC-0002")
    (src.parent / "DEC-0002 - Copy.md").write_text(
        src.read_text(encoding="utf-8").replace(
            "title: Review cloud costs every month", "title: Copy"
        ),
        encoding="utf-8",
    )
    assert "duplicate-id" in codes(config)


def test_unknown_tag(kb, config):
    edit(kb, "DEC-0002", "tags: [cost, governance]", "tags: [cost, budget]")
    assert "unknown-tag" in codes(config)


def test_active_card_needs_verification(kb, config):
    edit(
        kb,
        "DEC-0002",
        'verified: {by: "Team lead", date: "2026-02-05"}',
        'verified: {by: "", date: ""}',
    )
    assert "unverified" in codes(config)


def test_verification_cannot_be_in_the_future(kb, config):
    edit(kb, "DEC-0002", 'date: "2026-02-05"', 'date: "2026-12-31"')
    assert "bad-date" in codes(config)


def test_draft_needs_no_verification(config):
    # DEC-0004 is a draft with an empty verified block, and the example is clean.
    assert "unverified" not in codes(config)


def test_superseded_card_must_name_its_replacement(kb, config):
    edit(kb, "DEC-0001", "superseded_by: [DEC-0003]", "superseded_by: []")
    assert "superseded-by" in codes(config)


def test_supersession_must_be_consistent(kb, config):
    edit(kb, "DEC-0003", "supersedes: [DEC-0001]", "supersedes: []")
    assert "supersession" in codes(config)


def test_replaced_card_must_be_marked_superseded(kb, config):
    edit(kb, "DEC-0001", "status: superseded", "status: active")
    edit(kb, "DEC-0001", "review_by: 2026-01-16", "review_by: 2027-01-16")
    assert "supersession" in codes(config)


def test_broken_link(kb, config):
    edit(kb, "DEC-0002", "related: [FCT-0001]", "related: [FCT-0099]")
    assert "broken-link" in codes(config)


def test_one_way_link_is_a_warning(kb, config):
    edit(kb, "FCT-0001", "related: [DEC-0002]", "related: []")
    assert "one-way-link" in codes(config, "warning")
    assert validate(config, TODAY).ok


def test_decision_needs_a_source(kb, config):
    path = card_path(kb, "DEC-0002")
    text = path.read_text(encoding="utf-8")
    start = text.index("sources:")
    end = text.index("verified:")
    path.write_text(text[:start] + "sources: []\n" + text[end:], encoding="utf-8")
    assert "no-source" in codes(config)


def test_source_link_must_be_https(kb, config):
    edit(kb, "DEC-0002", "link: https://", "link: http://")
    assert "bad-source" in codes(config)


def test_body_must_open_with_summary(kb, config):
    edit(kb, "DEC-0002", "## Summary", "## Overview")
    assert "no-summary" in codes(config)


def test_long_summary_is_a_warning(kb, config):
    edit(kb, "DEC-0002", "The team reviews", "The team " + "really " * 130 + "reviews")
    assert "long-summary" in codes(config, "warning")


def test_overdue_review_is_a_warning(kb, config):
    edit(kb, "DEC-0002", "review_by: 2027-02-05", "review_by: 2026-06-01")
    assert "review-overdue" in codes(config, "warning")


@pytest.mark.parametrize(
    "text",
    ["write to data.lead@example.com", "call +44 20 7946 0958"],
)
def test_contact_details_are_blocked(kb, config, text):
    edit(kb, "ROL-0001", "Go to this role", f"Go to this role ({text})")
    assert "contact-details" in codes(config)


def test_contact_details_can_be_allowed(kb):
    edit(kb, "ROL-0001", "Go to this role", "Go to this role (data.lead@example.com)")
    cfg_path = kb / "kb.yaml"
    cfg_path.write_text(cfg_path.read_text() + "allow_contact_details: true\n")
    assert "contact-details" not in codes(load_config(kb))


def test_dates_and_numbers_are_not_phone_numbers(config):
    # The example is full of dates, times and amounts; none of them may trip the phone rule.
    assert "contact-details" not in codes(config)


def test_unreadable_front_matter(kb, config):
    (kb / "cards" / "facts" / "broken.md").write_text("no header here\n", encoding="utf-8")
    assert "unreadable" in codes(config)


def test_invalid_yaml(kb, config):
    (kb / "cards" / "facts" / "bad yaml.md").write_text(
        "---\nid: [unclosed\n---\n", encoding="utf-8"
    )
    assert "unreadable" in codes(config)


def test_unknown_classification(kb, config):
    edit(kb, "DEC-0002", "classification: internal", "classification: secret")
    assert "bad-classification" in codes(config)
