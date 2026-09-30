from teamkb.bundle import build_bundles, publishable
from teamkb.cards import load_cards
from teamkb.config import load_config
from teamkb.index import build_index

from .conftest import EXAMPLE, edit


def test_committed_example_index_is_current():
    config = load_config(EXAMPLE)
    cards, _ = load_cards(config.cards_path)
    assert build_index(config, cards, check=True) == []


def test_index_is_deterministic(kb, config):
    cards, _ = load_cards(config.cards_path)
    assert build_index(config, cards) == []  # copy of a current index: nothing to rewrite
    edit(kb, "DEC-0002", "The team reviews", "The team now reviews")
    cards, _ = load_cards(config.cards_path)
    assert build_index(config, cards, check=True) == ["INDEX.md", "manifest.json"]
    assert build_index(config, cards) == ["INDEX.md", "manifest.json"]
    assert build_index(config, cards, check=True) == []


def test_only_active_cards_at_or_below_ceiling_are_published(config):
    cards, _ = load_cards(config.cards_path)
    included, excluded = publishable(config, cards)
    ids = {c.id for c in included}
    assert "DEC-0001" not in ids  # superseded
    assert "DEC-0004" not in ids  # draft
    assert "FCT-0003" not in ids  # restricted, above the ceiling
    assert excluded == {"not active": 2, "above ceiling": 1}
    assert len(ids) == 9


def test_bundles_never_contain_unpublished_cards(tmp_path, config):
    cards, _ = load_cards(config.cards_path)
    result = build_bundles(config, cards, tmp_path)
    text = "\n".join(p.read_text(encoding="utf-8") for p in result.written)
    assert "Warehouse contract renewal terms" not in text  # restricted title never leaks
    assert "=== DEC-0004" not in text and "=== DEC-0001" not in text
    # Links are only rendered to published cards: DEC-0003 replaces DEC-0001, which is not.
    assert "Replaces:" not in text


def test_raising_the_ceiling_publishes_restricted_cards(tmp_path, kb):
    cfg = kb / "kb.yaml"
    cfg.write_text(
        cfg.read_text().replace("publish_ceiling: internal", "publish_ceiling: restricted")
    )
    config = load_config(kb)
    cards, _ = load_cards(config.cards_path)
    result = build_bundles(config, cards, tmp_path)
    assert "FCT-0003" in {c.id for c in result.included}


def test_bundle_files_and_version_line(tmp_path, config):
    cards, _ = load_cards(config.cards_path)
    result = build_bundles(config, cards, tmp_path)
    names = sorted(p.name for p in result.written)
    assert names[0] == "Harbour Data Team - 00 Catalogue.txt"
    assert "Harbour Data Team - Decisions.txt" in names
    for path in result.written:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[1].startswith("Version line: Harbour Data Team | ")
        assert "not a set of instructions" in lines[3]


def test_bundles_are_reproducible(tmp_path, config):
    cards, _ = load_cards(config.cards_path)
    first = {p.name: p.read_text() for p in build_bundles(config, cards, tmp_path / "a").written}
    second = {p.name: p.read_text() for p in build_bundles(config, cards, tmp_path / "b").written}
    assert first == second


def test_committed_example_bundles_are_current(tmp_path):
    config = load_config(EXAMPLE)
    cards, _ = load_cards(config.cards_path)
    result = build_bundles(config, cards, tmp_path)
    for path in result.written:
        committed = config.publish_path / path.name
        assert committed.read_text(encoding="utf-8") == path.read_text(encoding="utf-8")


def test_stale_bundle_is_reported_not_deleted(tmp_path, kb, config):
    cards, _ = load_cards(config.cards_path)
    build_bundles(config, cards, tmp_path)
    edit(kb, "TRM-0001", "status: active", "status: archived")
    cards, _ = load_cards(config.cards_path)
    result = build_bundles(config, cards, tmp_path)
    assert [p.name for p in result.stale] == ["Harbour Data Team - Glossary.txt"]
    assert (tmp_path / "Harbour Data Team - Glossary.txt").exists()


def test_unrelated_files_are_never_reported_stale(tmp_path, config):
    (tmp_path / "notes.txt").write_text("a file someone else put here")
    cards, _ = load_cards(config.cards_path)
    assert build_bundles(config, cards, tmp_path).stale == []


def test_oversized_bundle_is_flagged(tmp_path, kb):
    cfg = kb / "kb.yaml"
    cfg.write_text(cfg.read_text().replace("bundle_max_chars: 100000", "bundle_max_chars: 500"))
    config = load_config(kb)
    cards, _ = load_cards(config.cards_path)
    assert build_bundles(config, cards, tmp_path).oversized


def test_markdown_format(tmp_path, kb):
    cfg = kb / "kb.yaml"
    cfg.write_text(cfg.read_text().replace("publish_format: txt", "publish_format: md"))
    config = load_config(kb)
    cards, _ = load_cards(config.cards_path)
    assert all(p.suffix == ".md" for p in build_bundles(config, cards, tmp_path).written)
