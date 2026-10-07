# AGENTS.md: copilot-team-knowledge

Instructions for coding agents (and people) changing this repository. Read this first.

A verified knowledge layer between a team's documents and Microsoft 365 Copilot: small cards
with a source, an owner and a verification date; a validator and a publisher (`teamkb`) that
turn active cards into a few bundles; a Copilot agent or saved prompt that answers only from
those bundles. A local open-weight route (`teamkb ask`, `teamkb eval`) answers from the same
bundles.

## Commands

```bash
pip install -e ".[dev]"
ruff check .
pytest                                                    # offline
teamkb validate examples/harbour-data-team --quiet
teamkb index examples/harbour-data-team --check
teamkb eval examples/harbour-data-team evals/questions.jsonl --standin
for dir in evals/recordings/*/; do [ -d "$dir" ] && teamkb eval examples/harbour-data-team evals/questions.jsonl --model "$(basename "$dir" | sed 's/-/:/')" --recordings "$dir" --offline; done
```

## Layout

- `src/teamkb/cards.py`, `validate.py`: the card schema and its checks (see `docs/card-schema.md`)
- `src/teamkb/index.py`, `bundle.py`: `INDEX.md`, `manifest.json` and the published bundles
- `src/teamkb/local.py`: the local answering route and the citation check
- `src/teamkb/sharepoint.py`: `publish-sharepoint` through Microsoft Graph
- `copilot/agent/`: the declarative agent and its instructions; `copilot/prompt-only/`: saved prompts
- `skills/team-knowledge-curator/SKILL.md`: drafting cards from a final source with an agent
- `examples/harbour-data-team/`: a fictional team's knowledge base; `evals/questions.jsonl`: 12 questions

## Invariants: never weaken these

1. **Only active, verified cards at or below the ceiling are published.** Drafts and cards above
   the ceiling never reach `_published`.
2. **Agents propose; people decide.** Nothing in this repository sets a card to `active` or fills
   `verified`; only the card's owner does (design decisions, "Not done, on purpose").
3. **An answer that cites a card it was not given, or cites none, is withheld** on the local
   route. A `must_not_use` card or an e-mail address in an answer is a blocking failure.
4. **`publish-sharepoint` uploads only the publish folder**, with `Sites.Selected` on one site,
   and `--prune` removes only this knowledge base's own bundles.
5. **Copilot field limits are tested** (`tests/test_copilot_files.py`); keep instructions and
   descriptions within them.

## Working rules

- A wrong answer from Copilot or the local route becomes a question in `evals/questions.jsonl`
  before the fix.
- A change to the agent instructions, the bundles' format or the model makes recordings stale:
  re-record, never edit them by hand.
- Record every change in `CHANGELOG.md`; a design change goes in `docs/design-decisions.md`.
- The example describes a fictional team. Never add an employer's internal content.
  Commits carry no AI co-author trailers.
