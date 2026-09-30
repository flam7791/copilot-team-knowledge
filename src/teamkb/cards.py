"""Knowledge cards: the unit of curated team knowledge.

A card is one Markdown file with a YAML header (front matter) and a body that opens with a
``## Summary`` section. One durable item per card: a decision, a fact, a term, a project, a
meeting outcome, a how-to or a role.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CardType:
    name: str
    prefix: str
    folder: str
    label: str
    singular: str
    needs_source: bool


CARD_TYPES: dict[str, CardType] = {
    t.name: t
    for t in (
        CardType("decision", "DEC", "decisions", "Decisions", "Decision", True),
        CardType("fact", "FCT", "facts", "Facts", "Fact", True),
        CardType("meeting", "MTG", "meetings", "Meeting outcomes", "Meeting outcome", True),
        CardType("project", "PRJ", "projects", "Projects", "Project", False),
        CardType("howto", "HOW", "howto", "How-to", "How-to", False),
        CardType("term", "TRM", "glossary", "Glossary", "Term", False),
        CardType("role", "ROL", "roles", "Roles", "Role", False),
    )
}
PREFIX_TO_TYPE = {t.prefix: t for t in CARD_TYPES.values()}

STATUSES = ("draft", "active", "superseded", "archived")
REQUIRED_FIELDS = (
    "id",
    "type",
    "title",
    "status",
    "classification",
    "owner",
    "tags",
    "created",
    "updated",
)
ID_PATTERN = re.compile(r"^(?P<prefix>[A-Z]{3})-(?P<num>\d{4})$")
FORBIDDEN_TITLE_CHARS = set('\\/:*?"<>|#%')

# Control characters (tab, LF and CR allowed) and invisible characters. A generator script that
# writes escape sequences by mistake produces exactly these, and they break both humans and
# retrieval silently.
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u2060\ufeff]")


class CardError(ValueError):
    """The file cannot be read as a card at all."""


@dataclass
class Card:
    path: Path
    meta: dict[str, Any]
    body: str
    raw: str = field(repr=False)

    @property
    def id(self) -> str:
        return str(self.meta.get("id", ""))

    @property
    def type(self) -> str:
        return str(self.meta.get("type", ""))

    @property
    def title(self) -> str:
        return str(self.meta.get("title", ""))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    @property
    def classification(self) -> str:
        return str(self.meta.get("classification", ""))

    @property
    def tags(self) -> list[str]:
        tags = self.meta.get("tags") or []
        return [str(t) for t in tags] if isinstance(tags, list) else []

    def id_list(self, key: str) -> list[str]:
        value = self.meta.get(key) or []
        if isinstance(value, str):
            value = [value]
        return [str(v) for v in value] if isinstance(value, list) else []

    def date(self, key: str) -> dt.date | None:
        return as_date(self.meta.get(key))

    @property
    def verified(self) -> dict[str, Any]:
        value = self.meta.get("verified") or {}
        return value if isinstance(value, dict) else {}

    @property
    def summary(self) -> str:
        return section(self.body, "Summary")


def as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def split_front_matter(text: str) -> tuple[str, str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---\n"):
        raise CardError("file does not start with a '---' front-matter line")
    end = text.find("\n---\n", 4)
    if end == -1:
        if text.rstrip().endswith("\n---"):
            return text[4 : text.rstrip().rfind("\n---")], ""
        raise CardError("front matter is not closed with a '---' line")
    return text[4:end], text[end + 5 :]


def parse_card(path: Path) -> Card:
    raw = path.read_text(encoding="utf-8")
    raw = raw.replace("\r\n", "\n")
    header, body = split_front_matter(raw)
    try:
        meta = yaml.safe_load(header) or {}
    except yaml.YAMLError as exc:
        raise CardError(f"front matter is not valid YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise CardError("front matter must be a mapping of fields")
    return Card(path=path, meta=meta, body=body, raw=raw)


def section(body: str, heading: str) -> str:
    """Text of a ``## heading`` section, up to the next heading of level 1 or 2."""
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    rest = body[match.end() :]
    nxt = re.search(r"^#{1,2}\s", rest, re.MULTILINE)
    return (rest[: nxt.start()] if nxt else rest).strip()


def first_heading(body: str) -> str:
    match = re.search(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
    return match.group(1) if match else ""


def expected_filename(card_id: str, title: str) -> str:
    return f"{card_id} - {title}.md"


def load_cards(cards_dir: Path) -> tuple[list[Card], list[tuple[Path, str]]]:
    """All cards under ``cards_dir``, plus files that could not be parsed."""
    cards: list[Card] = []
    failures: list[tuple[Path, str]] = []
    for path in sorted(cards_dir.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        try:
            cards.append(parse_card(path))
        except (CardError, UnicodeDecodeError) as exc:
            failures.append((path, str(exc)))
    return cards, failures
