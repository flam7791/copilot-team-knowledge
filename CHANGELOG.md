# Changelog

Versions follow [semantic versioning](https://semver.org).

## 0.1.0

- Knowledge cards: seven types, YAML header, Summary-first body, controlled tags.
- `teamkb validate`: schema, links, supersession, verification, review dates, contact details,
  control and invisible characters.
- `teamkb index`: deterministic INDEX.md and manifest.json, with `--check` for CI.
- `teamkb bundle`: catalogue and one bundle per type, active cards at or below the publish
  ceiling only, with a version line and content hash.
- `teamkb new`: draft cards from a template with the next free ID.
- Copilot agent route (instructions and declarative agent manifest 1.8) and prompt-only route
  (ask and curate prompts).
- Fictional example knowledge base and a 12-question evaluation set.
