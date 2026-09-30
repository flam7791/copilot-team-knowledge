# Prompt-only route

For organisations where users have Microsoft 365 Copilot Chat but **cannot create or use
agents**. The knowledge base is the same; only the way Copilot reaches it changes.

| | Agent route | Prompt-only route |
|---|---|---|
| Where the rules live | Agent instructions | A saved prompt ([`ask.txt`](ask.txt)) in Prompt Gallery |
| How Copilot finds the knowledge | The `_published` folder is the agent's only knowledge | The user adds the catalogue and one or two bundles with "/" |
| Search scope | Limited to the configured folder | Copilot Chat can also search everything else the user can open; the prompt asks it to stay on the referenced files and label anything else |
| Read check | Not needed | First line of every reply echoes each file's version line |
| Curation | [`curate.txt`](curate.txt), then `teamkb` | Same |

Why bundles help here: a user can reference a few files with "/", not a hundred cards. The
catalogue tells Copilot what exists; the type bundles hold the full cards.

The prompts ask Copilot to echo each file's **version line** first. If Copilot silently fails to
read a referenced file, the missing version line shows it before anyone relies on the answer.
