# Design decisions

Each choice below is made for Microsoft 365 Copilot as it works today: it finds content by
search, returns only what the user may open, and answers from whatever it retrieves.

## How knowledge is stored

| Decision | Why |
|---|---|
| One item per Markdown file, with a YAML header | Readable by people, diffable, portable; no database to run |
| Seven typed cards (decision, fact, meeting, project, how-to, term, role), one folder per type | Typed items are easier to validate, review and retrieve than free-form notes |
| Every card opens with a self-contained Summary | Copilot retrieves passages, not folders; the passage it quotes must make sense on its own |
| A controlled tag vocabulary in `kb.yaml` | Stops tag sprawl; makes filtering reliable |
| Role cards, not person profiles | Responsibilities outlive people, and roles avoid building profiles of individuals |
| Cards summarise final sources and link to them | Copies of e-mail or chat would escape the sources' permissions and retention and multiply personal data |

## How knowledge becomes trustworthy

| Decision | Why |
|---|---|
| Copilot proposes cards; a named role verifies them before they are active | Extraction errors are common; confidence has to come from a check, not a claim |
| Curation only from final sources (approved minutes, sent decisions, published reports) | Drafts change; cards should not |
| Change by supersession, never by overwriting | History is kept; only the current card is published |
| A review date on every active card | Knowledge ages; overdue cards are flagged to curators and in answers |
| Rules enforced by `teamkb validate`, not written as prose for a model | A rule a script checks is a rule that holds |
| Indexes rebuilt by a script, with `--check` in CI | Deterministic, free, and never out of date unnoticed |

## How Copilot reaches it

| Decision | Why |
|---|---|
| Copilot reads bundles (a catalogue plus one file per type), not the cards | Agent Builder takes up to 100 SharePoint files; prompt-only users reference a handful |
| Only active cards at or below a classification ceiling are published | Drafts, replaced and restricted cards cannot leak through a folder they are never written to |
| Plain text by default, Markdown optional | Copilot surfaces handle Markdown unevenly (as of 2026); test before switching |
| A version line with a content hash in every bundle, echoed by the prompts | Shows at once whether Copilot actually read a referenced file |
| An agent route and a prompt-only route over the same bundles | Many organisations license Copilot Chat before they allow agents |

## Checks worth having

- **An evaluation set** built around the failures that matter most: a draft presented as a
  decision, restricted content, a replaced decision, a prompt-injection attempt.
- **A control-character check.** Generated files can pick up invisible characters (a script
  writing escape sequences by mistake is a classic cause). While this repository was being
  written, the check caught invisible characters in two of its own source files.

## Not done, on purpose

- **No write access for the agent.** Copilot proposes; people decide. A knowledge base that an
  agent can change by itself inherits every error and every injected instruction it reads.
- **No vector database or custom retrieval.** Copilot already retrieves; the gain here comes
  from what it retrieves from.
- **No automatic publication from SharePoint events.** Possible with Power Automate, but a
  scheduled or manual `teamkb bundle` keeps the publish step visible and reviewable.
