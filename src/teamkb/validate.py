"""Deterministic checks on a knowledge base.

Errors block publishing. Warnings are reported but do not block. Nothing here calls a language
model: the rules that keep the knowledge base trustworthy should not depend on one.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

from .cards import (
    CARD_TYPES,
    CONTROL_CHARS,
    FORBIDDEN_TITLE_CHARS,
    ID_PATTERN,
    PREFIX_TO_TYPE,
    REQUIRED_FIELDS,
    STATUSES,
    Card,
    as_date,
    expected_filename,
    first_heading,
    load_cards,
)
from .config import KBConfig

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w+])\+\d{1,3}(?:[\s.-]?\(?\d{1,4}\)?){2,5}(?!\w)")


@dataclass
class Issue:
    level: str  # "error" or "warning"
    code: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.code:18} {self.path}: {self.message}"


@dataclass
class Report:
    cards: list[Card] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(config: KBConfig, today: dt.date | None = None) -> Report:
    today = today or dt.date.today()
    report = Report()
    cards_dir = config.cards_path
    if not cards_dir.is_dir():
        report.issues.append(Issue("error", "no-cards-dir", str(cards_dir), "folder not found"))
        return report

    cards, failures = load_cards(cards_dir)
    report.cards = cards
    for path, reason in failures:
        report.issues.append(Issue("error", "unreadable", _rel(config, path), reason))

    by_id: dict[str, Card] = {}
    for card in cards:
        if card.id in by_id:
            report.issues.append(
                Issue(
                    "error",
                    "duplicate-id",
                    _rel(config, card.path),
                    f"{card.id} is also used by {_rel(config, by_id[card.id].path)}",
                )
            )
        elif card.id:
            by_id[card.id] = card

    for card in cards:
        report.issues.extend(_check_card(card, config, today))
    report.issues.extend(_check_links(cards, by_id, config))
    return report


def _rel(config: KBConfig, path: Path) -> str:
    try:
        return path.relative_to(config.root).as_posix()
    except ValueError:
        return path.as_posix()


def _check_card(card: Card, config: KBConfig, today: dt.date) -> list[Issue]:
    issues: list[Issue] = []
    where = _rel(config, card.path)

    def err(code: str, msg: str) -> None:
        issues.append(Issue("error", code, where, msg))

    def warn(code: str, msg: str) -> None:
        issues.append(Issue("warning", code, where, msg))

    bad = CONTROL_CHARS.search(card.raw)
    if bad:
        line = card.raw.count("\n", 0, bad.start()) + 1
        code = f"U+{ord(bad.group()):04X}"
        err("control-char", f"invisible or control character {code} on line {line}")

    missing = [f for f in REQUIRED_FIELDS if card.meta.get(f) in (None, "", [])]
    if missing:
        err("missing-field", ", ".join(missing))

    ctype = CARD_TYPES.get(card.type)
    if card.type and not ctype:
        err("bad-type", f"'{card.type}' is not one of {', '.join(CARD_TYPES)}")

    match = ID_PATTERN.match(card.id)
    if card.id and not match:
        err("bad-id", f"'{card.id}' does not match PREFIX-0000")
    elif match and ctype and match.group("prefix") != ctype.prefix:
        err("id-type-mismatch", f"{card.id} should start with {ctype.prefix} for a {card.type}")
    elif match and match.group("prefix") not in PREFIX_TO_TYPE:
        err("bad-id", f"unknown prefix {match.group('prefix')}")

    if ctype and card.path.parent.name != ctype.folder:
        err("wrong-folder", f"a {card.type} belongs in cards/{ctype.folder}/")

    if card.title:
        bad_chars = sorted(set(card.title) & FORBIDDEN_TITLE_CHARS)
        if bad_chars:
            err("title-chars", f"title contains {' '.join(bad_chars)} (not safe in file names)")
        if card.id and card.path.name != expected_filename(card.id, card.title):
            err("filename", f"expected '{expected_filename(card.id, card.title)}'")
        if len(card.path.name) > 100:
            warn("long-filename", "file name over 100 characters; SharePoint paths have limits")

    if card.status and card.status not in STATUSES:
        err("bad-status", f"'{card.status}' is not one of {', '.join(STATUSES)}")
    if card.classification and card.classification not in config.classifications:
        err("bad-classification", f"'{card.classification}' is not one of {config.classifications}")

    unknown_tags = [t for t in card.tags if t not in config.tags]
    if unknown_tags:
        err("unknown-tag", f"{', '.join(unknown_tags)} not in the vocabulary in kb.yaml")
    if card.tags and not 1 <= len(card.tags) <= 7:
        warn("tag-count", f"{len(card.tags)} tags; use one to seven")

    for key in ("created", "updated", "review_by"):
        if card.meta.get(key) not in (None, "") and card.date(key) is None:
            err("bad-date", f"{key} is not a YYYY-MM-DD date")
    created, updated = card.date("created"), card.date("updated")
    if created and updated and updated < created:
        err("bad-date", "updated is earlier than created")

    verified = card.verified
    v_date = verified.get("date")
    needs_check = card.status in ("active", "superseded", "archived")
    if needs_check and (not verified.get("by") or not v_date):
        err("unverified", f"cannot be {card.status} until verified.by and verified.date are set")
    if v_date:
        vd = as_date(v_date)
        if vd is None:
            err("bad-date", "verified.date is not a YYYY-MM-DD date")
        elif vd > today:
            err("bad-date", "verified.date is in the future")

    if card.status == "active":
        review_by = card.date("review_by")
        if review_by is None:
            err("no-review-date", "an active card needs review_by")
        elif review_by < today:
            warn("review-overdue", f"review was due {review_by.isoformat()}")

    if card.status == "superseded" and not card.id_list("superseded_by"):
        err("superseded-by", "a superseded card must name superseded_by")

    sources = card.meta.get("sources") or []
    if ctype and ctype.needs_source and not sources:
        err("no-source", f"a {card.type} card needs at least one source")
    if not isinstance(sources, list):
        err("bad-source", "sources must be a list of {title, link}")
    else:
        for i, src in enumerate(sources, 1):
            if not isinstance(src, dict) or not src.get("title"):
                err("bad-source", f"source {i} needs a title")
            elif src.get("link") and not str(src["link"]).startswith("https://"):
                err("bad-source", f"source {i} link must start with https://")

    if first_heading(card.body) != "Summary":
        err("no-summary", "the body must open with a '## Summary' section")
    else:
        words = len(card.summary.split())
        if words == 0:
            err("no-summary", "the Summary section is empty")
        elif words > config.summary_max_words:
            limit = config.summary_max_words
            warn("long-summary", f"summary is {words} words; keep it under {limit}")

    if not config.allow_contact_details:
        text = card.body + "\n" + str(card.meta.get("owner", ""))
        if EMAIL.search(text):
            err("contact-details", "e-mail address in the card; record roles, not contact details")
        if PHONE.search(text):
            err("contact-details", "phone number in the card; record roles, not contact details")
    return issues


def _check_links(cards: list[Card], by_id: dict[str, Card], config: KBConfig) -> list[Issue]:
    issues: list[Issue] = []
    for card in cards:
        where = _rel(config, card.path)
        for key in ("related", "supersedes", "superseded_by"):
            for target in card.id_list(key):
                if target not in by_id:
                    msg = f"{key}: {target} not found"
                    issues.append(Issue("error", "broken-link", where, msg))
        for target in card.id_list("related"):
            other = by_id.get(target)
            if other and card.id not in other.id_list("related"):
                issues.append(
                    Issue(
                        "warning",
                        "one-way-link",
                        where,
                        f"{card.id} lists {target} as related, but not the other way round",
                    )
                )
        for target in card.id_list("superseded_by"):
            newer = by_id.get(target)
            if newer and card.id not in newer.id_list("supersedes"):
                issues.append(
                    Issue(
                        "error",
                        "supersession",
                        where,
                        f"{target} must list {card.id} under supersedes",
                    )
                )
        for target in card.id_list("supersedes"):
            older = by_id.get(target)
            if older and older.status != "superseded":
                issues.append(
                    Issue(
                        "error",
                        "supersession",
                        where,
                        f"{target} is replaced by {card.id} but its status is '{older.status}'",
                    )
                )
    return issues
