"""Command line: ``teamkb new | validate | index | bundle``."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import __version__
from .bundle import build_bundles
from .cards import CARD_TYPES, FORBIDDEN_TITLE_CHARS, ID_PATTERN, expected_filename, load_cards
from .config import ConfigError, load_config
from .index import build_index
from .validate import validate

TEMPLATE = """---
id: {id}
type: {type}
title: {title}
status: draft
classification: {classification}
owner: {owner}
tags: []
sources: []
verified: {{by: "", date: ""}}
review_by: {review_by}
related: []
supersedes: []
superseded_by: []
created: {today}
updated: {today}
---
## Summary

{summary_hint}

## Details

-

## Evidence

- What the sources say, kept separate from interpretation.
"""

SUMMARY_HINTS = {
    "decision": "What was decided, by whom, when, and why - in two or three sentences that make "
    "sense on their own.",
    "fact": "The fact, with its figure, unit and date, as the source gives it.",
    "meeting": "The meeting, its date, and the outcomes that matter after it.",
    "project": "What the project delivers, for whom, current status and the next milestone.",
    "howto": "The task and the shortest correct way to do it.",
    "term": "The term, what it means in this team, and what it does not mean.",
    "role": "The role, what it is responsible for, and when to go to it. No personal details.",
}


def _today(args: argparse.Namespace) -> dt.date:
    return dt.date.fromisoformat(args.today) if getattr(args, "today", None) else dt.date.today()


def _add_months(day: dt.date, months: int) -> dt.date:
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    for d in (day.day, 30, 29, 28):
        try:
            return dt.date(year, month, d)
        except ValueError:
            continue
    raise ValueError("unreachable")


def cmd_new(args: argparse.Namespace) -> int:
    config = load_config(Path(args.kb))
    ctype = CARD_TYPES[args.type]
    title = args.title.strip()
    bad = sorted(set(title) & FORBIDDEN_TITLE_CHARS)
    if bad:
        print(f"Title contains {' '.join(bad)}; choose a file-name-safe title.", file=sys.stderr)
        return 2
    cards, _ = load_cards(config.cards_path) if config.cards_path.exists() else ([], [])
    numbers = [
        int(m.group("num"))
        for c in cards
        if (m := ID_PATTERN.match(c.id)) and m.group("prefix") == ctype.prefix
    ]
    card_id = f"{ctype.prefix}-{max(numbers, default=0) + 1:04d}"
    today = _today(args)
    folder = config.cards_path / ctype.folder
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / expected_filename(card_id, title)
    path.write_text(
        TEMPLATE.format(
            id=card_id,
            type=ctype.name,
            title=title,
            classification=args.classification or config.publish_ceiling,
            owner=args.owner,
            review_by=_add_months(today, config.review_months).isoformat(),
            today=today.isoformat(),
            summary_hint=SUMMARY_HINTS[ctype.name],
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(path)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_config(Path(args.kb))
    report = validate(config, _today(args))
    for issue in report.issues:
        if issue.level == "error" or not args.quiet:
            print(issue)
    print(
        f"{len(report.cards)} card(s): {len(report.errors)} error(s), "
        f"{len(report.warnings)} warning(s)"
    )
    if args.strict and report.warnings:
        return 1
    return 0 if report.ok else 1


def cmd_index(args: argparse.Namespace) -> int:
    config = load_config(Path(args.kb))
    cards, _ = load_cards(config.cards_path)
    stale = build_index(config, cards, check=args.check)
    if args.check:
        if stale:
            print(f"Out of date: {', '.join(stale)}. Run: teamkb index {args.kb}")
            return 1
        print("Index is up to date.")
        return 0
    print(f"Updated: {', '.join(stale)}" if stale else "Index already up to date.")
    return 0


def cmd_bundle(args: argparse.Namespace) -> int:
    config = load_config(Path(args.kb))
    report = validate(config, _today(args))
    if not report.ok:
        for issue in report.errors:
            print(issue)
        print("Not published: fix the errors above first (teamkb validate).")
        return 1
    out = Path(args.out) if args.out else None
    result = build_bundles(config, report.cards, out)
    for path in result.written:
        print(f"wrote {path}")
    print(
        f"{len(result.included)} card(s) published; excluded: "
        + ", ".join(f"{n} {why}" for why, n in result.excluded.items())
    )
    for path in result.oversized:
        print(
            f"WARNING {path.name} exceeds {config.bundle_max_chars} characters; split it, "
            "or test that Copilot still reads it in full."
        )
    for path in result.stale:
        if args.prune:
            path.unlink()
            print(f"removed stale bundle {path.name}")
        else:
            print(f"stale bundle {path.name} (no longer produced; remove it or use --prune)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teamkb", description="Curated team knowledge for Microsoft 365 Copilot."
    )
    parser.add_argument("--version", action="version", version=f"teamkb {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def with_kb(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p.add_argument("kb", help="knowledge-base folder (the one holding kb.yaml)")
        p.add_argument("--today", help=argparse.SUPPRESS)
        return p

    p = with_kb(sub.add_parser("new", help="create a draft card from the template"))
    p.add_argument("type", choices=list(CARD_TYPES))
    p.add_argument("title")
    p.add_argument("--owner", default="(role)", help="owning role, not a person's contact details")
    p.add_argument("--classification")
    p.set_defaults(func=cmd_new)

    p = with_kb(sub.add_parser("validate", help="check every card"))
    p.add_argument("--strict", action="store_true", help="fail on warnings too")
    p.add_argument("--quiet", action="store_true", help="print errors only")
    p.set_defaults(func=cmd_validate)

    p = with_kb(sub.add_parser("index", help="rebuild INDEX.md and manifest.json"))
    p.add_argument("--check", action="store_true", help="fail if the index is out of date")
    p.set_defaults(func=cmd_index)

    p = with_kb(sub.add_parser("bundle", help="build the files Copilot reads"))
    p.add_argument("--out", help="output folder (default: publish_dir in kb.yaml)")
    p.add_argument("--prune", action="store_true", help="delete bundles no longer produced")
    p.set_defaults(func=cmd_bundle)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
