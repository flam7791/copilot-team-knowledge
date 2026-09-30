from teamkb.cards import parse_card
from teamkb.cli import main

from .conftest import EXAMPLE


def test_validate_example(capsys):
    assert main(["validate", str(EXAMPLE), "--today", "2026-09-30"]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_index_check_example():
    assert main(["index", str(EXAMPLE), "--check"]) == 0


def test_new_creates_next_draft(kb, capsys):
    assert (
        main(["new", str(kb), "decision", "Archive unused dashboards", "--today", "2026-09-30"])
        == 0
    )
    path = kb / "cards" / "decisions" / "DEC-0005 - Archive unused dashboards.md"
    assert capsys.readouterr().out.strip().endswith(path.name)
    card = parse_card(path)
    assert card.status == "draft"
    assert card.classification == "internal"
    assert str(card.meta["review_by"]) == "2027-09-30"


def test_new_draft_fails_validation_until_completed(kb, capsys):
    main(["new", str(kb), "fact", "Number of dashboards", "--today", "2026-09-30"])
    assert main(["validate", str(kb), "--today", "2026-09-30"]) == 1
    out = capsys.readouterr().out
    assert "missing-field" in out and "no-source" in out


def test_new_rejects_unsafe_title(kb):
    assert main(["new", str(kb), "term", "What: is this?"]) == 2


def test_bundle_refuses_when_invalid(kb, tmp_path, capsys):
    main(["new", str(kb), "fact", "Number of dashboards", "--today", "2026-09-30"])
    out = tmp_path / "out"
    assert main(["bundle", str(kb), "--out", str(out), "--today", "2026-09-30"]) == 1
    assert "Not published" in capsys.readouterr().out
    assert not out.exists()


def test_bundle_prune(kb, tmp_path):
    (tmp_path / "Harbour Data Team - Old.txt").write_text("x\nBuilt by teamkb bundle. old\n")
    assert (
        main(["bundle", str(kb), "--out", str(tmp_path), "--prune", "--today", "2026-09-30"]) == 0
    )
    assert not (tmp_path / "Harbour Data Team - Old.txt").exists()


def test_config_error_exit_code(tmp_path, capsys):
    assert main(["validate", str(tmp_path)]) == 2
