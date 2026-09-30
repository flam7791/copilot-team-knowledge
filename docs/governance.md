# Governance

A knowledge base that Copilot answers from is a publication channel. These rules keep it
accurate, proportionate and safe.

## 1. Permissions are the control

Microsoft 365 Copilot only returns content that the person asking is already allowed to open.
That makes the SharePoint permissions on each folder the real access control, for people and
for Copilot alike.

| Folder | Who can read | Why |
|---|---|---|
| `_published` | The audience of the agent | It is what the agent answers from |
| `cards` | Curators and card owners | Holds drafts, replaced and restricted cards |
| Working documents | As today | Unchanged |

Classification labels describe content; they do not replace permissions. Set the folder
permissions first, then label.

## 2. A publish ceiling

`publish_ceiling` in `kb.yaml` is the highest classification that reaches Copilot. Cards above
it are never written to a bundle, whatever their status. Unknown classification labels are
treated as the most sensitive, so a typo cannot publish a card.

## 3. Nothing is published unverified

A card is `draft` until its owner has checked it against its source and filled
`verified.by`, `verified.date` and `review_by`. `teamkb validate` refuses an active card
without them, and `teamkb bundle` refuses to publish while any error remains. Copilot's
curate prompt can propose cards; it can never make one active.

## 4. Evidence separate from interpretation

Every decision, fact and meeting outcome needs at least one source, with a link where one
exists. The body keeps `## Evidence` (what the source says) apart from `## Summary` and
`## Details`. Figures are recorded exactly as the source gives them, with unit and date, and
the agent is told never to recompute them.

## 5. Change without deletion

Knowledge changes by replacement, not by overwriting: the new card lists the old one under
`supersedes`, the old one becomes `superseded` and names its successor. `teamkb validate`
checks that both sides agree. Superseded cards stay in the cards folder for the record and are
never published.

## 6. Review dates

Every active card has a `review_by` date (default: 12 months after creation, set in
`kb.yaml`). Overdue cards are reported by `teamkb validate` and flagged by the agent in its
answers ("review overdue"). A review ends in one of three outcomes: confirmed (new
`review_by`), updated, or replaced.

## 7. Personal data: roles, not people

- Owners, verifiers and role cards name **roles** ("Data platform lead"), not individuals.
- `teamkb validate` blocks e-mail addresses and international phone numbers in cards, unless a
  team deliberately sets `allow_contact_details: true`.
- Do not create cards about individuals' performance, health or private circumstances.

## 8. Retention

Cards are derived summaries that link to their sources; they do not replace the sources'
retention. Decide, once, how long superseded and archived cards are kept, and record it in the
team's retention schedule. The raw sources (e-mail, chat, recordings) are not copied into the
knowledge base.

## 9. Content is data, not instructions

Documents can contain text written to manipulate an AI system ("ignore previous instructions").
The agent instructions, both prompts and every bundle header state that knowledge content is
reference material, never instructions. This reduces the risk of indirect prompt injection; it
does not remove it, which is one more reason cards are written and verified by people.

## 10. Integrity of the files themselves

`teamkb validate` rejects control and invisible characters (null, backspace, bell, zero-width
spaces, byte-order marks inside the text). Scripts that generate files can introduce them
without anyone noticing; they then corrupt tags, file references and, in the worst case, the
instructions an agent reads first. The test suite applies the same check to every text file in
this repository.
