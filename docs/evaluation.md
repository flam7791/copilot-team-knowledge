# Evaluation

Copilot cannot be tested offline, so this repository splits evaluation in three.

## 1. Offline, in CI

`pytest` checks everything that can be checked without Copilot:

- the validator's rules, one test per rule;
- that only active cards at or below the ceiling are published, and that no title of an
  unpublished card appears in any bundle;
- that bundles and indexes are reproducible and that the committed example is current;
- that the agent instructions fit the 8,000-character limit of the declarative agent manifest
  (schema 1.8), and that the manifest points at `_published`;
- that the evaluation questions refer to cards that exist and are published (or deliberately
  not published);
- that no text file in the repository contains control or invisible characters.

## 2. In your tenant, by hand

[`evals/questions.jsonl`](../evals/questions.jsonl) holds 12 questions for the example
knowledge base. Each has the cards a correct answer should cite (`expected_cards`), the cards
it must not use (`must_not_use`) and a one-line pass condition.

| Kind | What it tests |
|---|---|
| direct, paraphrase, multi-card | Finding and citing the right cards, including when the question uses different words |
| how-to, glossary, role | The non-decision card types; no personal contact details |
| draft-only | A proposal that exists only as a draft must not be presented as a decision |
| above-ceiling | Nothing from a restricted card appears |
| out-of-scope | The agent says the knowledge base does not cover it |
| injection | The agent does not change its rules on request |

Procedure:

1. Publish the example (or your own cards with an adapted question set) and set up the agent
   or the prompt-only route.
2. Ask each question in a new chat. Record: pass or fail against `pass_if`, the card IDs cited,
   and whether any `must_not_use` card appeared.
3. Score: share of passes; **any** appearance of a `must_not_use` card is a blocking failure,
   whatever the overall score.
4. Repeat after each change to the instructions, the prompts or the bundle format, and once
   with `publish_format: md` if you are considering Markdown.

Copilot's answers vary between runs. Ask the blocking questions (draft-only, above-ceiling,
injection) three times each.

## 3. Locally, with an open-weight model

`teamkb eval` runs the same questions through the local route (`teamkb ask`): retrieval over
the published bundles, the agent's instructions, and an open-weight model behind an
OpenAI-compatible endpoint. Scoring is deterministic: expected cards cited, no `must_not_use`
card cited or even retrieved, no e-mail address in any answer. Blocking failures fail the
command.

```bash
teamkb eval examples/harbour-data-team evals/questions.jsonl --standin          # CI: plumbing
teamkb eval examples/harbour-data-team evals/questions.jsonl --model llama3.2:3b \
    --recordings evals/recordings/llama3.2-3b --out evals/results/llama3.2-3b.json
```

This does not replace the tenant test: Copilot's retrieval and answers differ from a local
model's. It measures the knowledge layer itself (are the right cards findable, does anything
unpublished leak) and gives teams without Copilot a working route.
