# Operations: Team knowledge layer

Owner: _name_ · Backup: _name_ · Review: every three months

## Monitoring

| Signal | Source | Frequency | Act when |
|---|---|---|---|
| Cards overdue for review | `teamkb validate` warnings | weekly | any card past `review_by` |
| Validation errors | `teamkb validate --strict` in CI or before each publish | each publish | any: nothing is published |
| Answer quality | the 12 evaluation questions, in the tenant and with `teamkb eval` | after any change to instructions or bundle format; quarterly | any blocking failure |
| Unpublished content reached | evaluation `must_not_use` checks | each evaluation | any: stop the agent, check the publish folder |

## Runbook

- A wrong answer relied on: find the card, correct or retire it, republish, add a question to the evaluation set.
- Restricted content in the publish folder: remove the bundle, check `publish_ceiling` and the card labels, rebuild.
- Copilot behaviour changes after a platform update: rerun the evaluation questions in the tenant.

## Change and release

- Every change runs the tests and the evaluation in CI; a recorded model run is re-recorded when the prompt or the model changes.
- Versions and changes are listed in CHANGELOG.md; the previous release tag is the rollback.
