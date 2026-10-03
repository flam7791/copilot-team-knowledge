# Publishing to SharePoint through Microsoft Graph

`teamkb publish-sharepoint` uploads the bundles to the SharePoint folder the Copilot agent reads,
so publishing can run from a pipeline rather than from a OneDrive-synced laptop:

```bash
teamkb validate examples/harbour-data-team --strict
teamkb bundle   examples/harbour-data-team --prune
TEAMKB_GRAPH_CLIENT_SECRET=... teamkb publish-sharepoint examples/harbour-data-team --prune
```

Only files from the publish folder are uploaded. Drafts, replaced decisions and restricted cards
are never written there, so they cannot be published even by mistake. `--prune` deletes only
this knowledge base's own bundles that are no longer produced (file names starting with the
knowledge base's name), never other files in the folder.

## Configuration (kb.yaml)

```yaml
sharepoint:
  tenant_id: 00000000-0000-0000-0000-000000000000
  client_id: 11111111-1111-1111-1111-111111111111
  site: contoso.sharepoint.com:/sites/harbour-data
  library: Documents
  folder: Team knowledge/_published     # the folder named in the agent manifest
```

The folder must be the one in `copilot/agent/declarativeAgent.json`
(`capabilities[OneDriveAndSharePoint].items_by_url`).

## App registration (least privilege)

1. Entra admin centre > App registrations > New registration: `teamkb-publisher`, single tenant.
2. API permissions > Microsoft Graph > Application > **`Sites.Selected`**, admin consent. On its
   own it reaches no site.
3. A SharePoint or Global administrator grants **write** on the one team site:

   ```http
   POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions
   {"roles": ["write"],
    "grantedToIdentities": [{"application": {"id": "<client id>", "displayName": "teamkb-publisher"}}]}
   ```

4. A client secret (pilot) or certificate (production), kept in the pipeline's secret store as
   `TEAMKB_GRAPH_CLIENT_SECRET`.

## As a pipeline

```yaml
# .github/workflows/publish.yml (or the equivalent Azure DevOps pipeline)
on:
  push:
    branches: [main]
    paths: ["kb/**"]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install .
      - run: teamkb validate kb --strict && teamkb index kb --check && teamkb bundle kb --prune
      - run: teamkb publish-sharepoint kb --prune
        env:
          TEAMKB_GRAPH_CLIENT_SECRET: ${{ secrets.TEAMKB_GRAPH_CLIENT_SECRET }}
```

Card owners still verify every card before it is published; the pipeline only automates the
copy, after the same validation that blocks a release.
