import datetime as dt
import shutil
from pathlib import Path

import pytest

from teamkb.config import load_config

REPO = Path(__file__).resolve().parents[1]
EXAMPLE = REPO / "examples" / "harbour-data-team"
TODAY = dt.date(2026, 9, 30)


@pytest.fixture
def kb(tmp_path: Path) -> Path:
    """A writable copy of the example knowledge base."""
    target = tmp_path / "kb"
    shutil.copytree(EXAMPLE, target)
    return target


@pytest.fixture
def config(kb: Path):
    return load_config(kb)


def card_path(kb: Path, card_id: str) -> Path:
    matches = list((kb / "cards").rglob(f"{card_id} - *.md"))
    assert len(matches) == 1, f"{card_id} not found"
    return matches[0]


def edit(kb: Path, card_id: str, old: str, new: str) -> Path:
    path = card_path(kb, card_id)
    text = path.read_text(encoding="utf-8")
    assert old in text, f"'{old}' not in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path
