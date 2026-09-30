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
    link: https://contoso.sharepoint.com/sites/harbour-data/Shared%20Documents/Minutes/2026-03-12%20Architecture%20review.docx
verified: {by: "Data platform lead", date: "2026-03-14"}
review_by: 2027-03-14
related: [MTG-0001, PRJ-0001]
supersedes: [DEC-0001]
superseded_by: []
created: 2026-03-14
updated: 2026-03-14
---
## Summary

Since 16 March 2026, reporting dashboards refresh every four hours (00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UTC). Business users asked for same-day figures, and the move to a usage-based warehouse plan removed the reason for a single nightly load.

## Details

- Replaces the nightly refresh (DEC-0001).
- Refreshes that fail are retried once after 30 minutes; a second failure alerts the data platform lead.

## Evidence

- Decided at the 12 March 2026 architecture review (MTG-0001).
- The cost impact was estimated in the same meeting at under 5% of monthly spend; this is an estimate, not a measured figure.
