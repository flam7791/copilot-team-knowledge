---
id: DEC-0001
type: decision
title: Refresh reporting dashboards nightly
status: superseded
classification: internal
owner: Data platform lead
tags: [dashboards, reporting]
sources:
  - title: "Architecture review minutes, 14 January 2025"
    link: https://contoso.sharepoint.com/sites/harbour-data/Shared%20Documents/Minutes/2025-01-14%20Architecture%20review.docx
verified: {by: "Data platform lead", date: "2025-01-16"}
review_by: 2026-01-16
related: []
supersedes: []
superseded_by: [DEC-0003]
created: 2025-01-16
updated: 2026-03-14
---
## Summary

Reporting dashboards were refreshed once a night, at 02:00 UTC, to keep warehouse load outside working hours. Replaced in March 2026 by a four-hourly refresh (DEC-0003).

## Details

- Chosen when the warehouse ran on a fixed-capacity plan and daytime loads slowed analyst queries.

## Evidence

- The January 2025 architecture review minutes record the decision and the 02:00 UTC slot.
