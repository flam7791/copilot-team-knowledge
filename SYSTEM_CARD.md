# System card: copilot-team-knowledge

| | |
|---|---|
| Pattern | P6 curated knowledge layer for an enterprise assistant ([ai-engineering-framework](https://github.com/flam7791/ai-engineering-framework)) |
| Models | Microsoft 365 Copilot (agent or saved prompts); optionally a local open-weight model over the same bundles (`teamkb ask`) |
| Classification ceiling | `publish_ceiling` in `kb.yaml` |

## Intended use

Make a team's assistant answer from what the team has verified: decisions, facts, how-tos, terms
and roles kept as small cards with a source, an owner and review dates.

## Out of scope

Replacing the source documents; answering from unverified drafts; storing personal contact
details (role cards point to roles, not people).

## Data

Only active cards at or below the ceiling are published to the folder the assistant reads;
drafts, replaced decisions and restricted cards are never written there. The local route reads
the same folder only.

## How it can fail

- Copilot retrieves from the published files in its own way; answers can still vary between runs
  (the tenant procedure asks the blocking questions three times).
- A card that is wrong but verified is answered confidently: the owner's verification and review
  dates are the control.
- A small local model may cite the wrong card or none; such answers are withheld by the check in
  code.

## Evaluation

Offline tests for every validator rule and for what is published; 12 evaluation questions with
expected and forbidden cards, run by hand in the tenant and in code through the local route,
where any use of an unpublished card or an e-mail address is a blocking failure.

## Human oversight

Card owners verify every card before it is published; the assistant can only propose draft cards,
which a curator adds.
