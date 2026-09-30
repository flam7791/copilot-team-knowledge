# Card schema

A card is one Markdown file named `<ID> - <Title>.md`, stored in the folder for its type under
`cards/`.

```markdown
---
id: DEC-0003
type: decision
title: Refresh reporting dashboards every four hours
status: active
classification: internal
owner: Data platform lead
tags: [dashboards, reporting, data-platform]
sources:
  - title: "Architecture review minutes, 12 March 2026"
    link: https://contoso.sharepoint.com/sites/harbour-data/Shared%20Documents/Minutes/...
verified: {by: "Data platform lead", date: "2026-03-14"}
review_by: 2027-03-14
related: [MTG-0001, PRJ-0001]
supersedes: [DEC-0001]
superseded_by: []
created: 2026-03-14
updated: 2026-03-14
---
## Summary

Two or three sentences that make sense on their own.

## Details

## Evidence
```

## Fields

| Field | Required | Rule |
|---|---|---|
| `id` | yes | `PREFIX-0000`; the prefix must match the type |
| `type` | yes | `decision` (DEC), `fact` (FCT), `meeting` (MTG), `project` (PRJ), `howto` (HOW), `term` (TRM), `role` (ROL) |
| `title` | yes | No `\ / : * ? " < > \| # %`; the file name must be `<id> - <title>.md` |
| `status` | yes | `draft`, `active`, `superseded`, `archived` |
| `classification` | yes | One of `classifications` in `kb.yaml` |
| `owner` | yes | A role, not a person's contact details |
| `tags` | yes | One to seven, from the `tags` vocabulary in `kb.yaml` |
| `sources` | decision, fact, meeting | List of `{title, link}`; links must be `https://` |
| `verified` | active, superseded, archived | `{by: role, date: YYYY-MM-DD}`; not in the future |
| `review_by` | active | Date; overdue is a warning |
| `related` | no | Card IDs; should be listed on both cards (warning if one-way) |
| `supersedes` / `superseded_by` | when replacing | Both sides must agree; the old card's status is `superseded` |
| `created`, `updated` | yes | Dates; `updated` not earlier than `created` |

## Body

- Must open with `## Summary`. Keep it under 120 words (configurable): it is the passage most
  likely to be retrieved and quoted.
- `## Details` for anything worth keeping that does not fit the summary.
- `## Evidence` for what the sources say, kept apart from interpretation.

## Types

| Type | Folder | Use for |
|---|---|---|
| decision | `decisions` | Something the team agreed, with who, when and why |
| fact | `facts` | A figure, rule or state of affairs with a source |
| meeting | `meetings` | The outcomes of a meeting that matter afterwards |
| project | `projects` | What a project delivers, status and next milestone |
| howto | `howto` | The shortest correct way to do a recurring task |
| term | `glossary` | What a word means in this team |
| role | `roles` | A responsibility and when to go to it |
