# Changelog

Versions follow [semantic versioning](https://semver.org).

## 0.2.0

- `teamkb ask`: answer from the published bundles with a local open-weight model (Ollama or any
  OpenAI-compatible endpoint), following the Copilot agent's own instructions; answers citing a
  card that was not given, or none, are withheld. Standard library only.
- `teamkb eval`: the 12 evaluation questions scored in code through the local route; any use of
  an unpublished card or an e-mail address in an answer is a blocking failure. Record and replay.
- CI runs the evaluation (stand-in, plus any recorded model runs) and a dependency scan.

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
