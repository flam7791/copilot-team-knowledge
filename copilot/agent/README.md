# Copilot agent route

For teams whose users can create or use agents in Microsoft 365 Copilot.

The agent is a **declarative agent**: instructions plus one knowledge source, the
`_published` folder produced by `teamkb bundle`. It reads; it never writes. New knowledge
reaches it only through the curation workflow (draft card, owner verification, rebuild).

## Option A: Agent Builder (no code)

1. In Microsoft 365 Copilot, create an agent.
2. **Instructions:** paste the content of [`instructions.txt`](instructions.txt) (about
   3,800 characters; the limit is 8,000).
3. **Knowledge:** add the SharePoint folder that holds the published bundles
   (`.../YOUR-KB/_published`), and nothing else. Do not add the `cards` folder: drafts and
   replaced cards live there.
4. Turn web search off, so answers come from the team's knowledge only.
5. Add the conversation starters from [`declarativeAgent.json`](declarativeAgent.json), adapted
   to your team.
6. Share the agent with the same people who can read the `_published` folder. Copilot only
   returns content a user is already allowed to open, so the folder permissions decide who
   sees what, not the agent.

## Option B: Microsoft 365 Agents Toolkit (manifest in source control)

Create a declarative-agent project with the Agents Toolkit, then replace its
`declarativeAgent.json` and instruction file with the two files in this folder and set the
`_published` folder URL. The `$[file('instructions.txt')]` reference keeps the instructions in
their own file, so they can be reviewed like code.

## Checks before sharing

- Run the question set in [`../../evals/questions.jsonl`](../../evals/questions.jsonl), adapted
  to your cards (see [`../../docs/evaluation.md`](../../docs/evaluation.md)).
- Ask one question whose answer is only in a **draft** card and one whose answer is only in a
  card **above the publish ceiling**. The agent must say it does not know.
- Ask about a decision that was replaced. The agent must give the newer one.
