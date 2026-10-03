"""Publish the bundles to the SharePoint folder the Copilot agent reads, through Microsoft Graph.

Without this, the published files reach SharePoint through a OneDrive-synced folder on someone's
laptop. With it, `teamkb publish-sharepoint` runs from a pipeline: validate, bundle, upload.

- App-only access (client credentials) with **Sites.Selected**, granted *write* on the one site:
  the publisher can touch no other site.
- Only files from the publish folder are uploaded, so drafts and restricted cards cannot be sent
  even by mistake: they are never written there.
- `--prune` removes bundles of this knowledge base that are no longer produced (a card type with
  no active card left), and nothing else: only files whose name starts with the knowledge base's
  name are candidates.

Standard library only (urllib), like the rest of the package.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import KBConfig

GRAPH = "https://graph.microsoft.com/v1.0"
REQUIRED = ("tenant_id", "client_id", "site", "folder")


class PublishError(RuntimeError):
    pass


Send = Callable[[str, str, dict, bytes | None], tuple[int, bytes]]


def _urllib_send(method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except urllib.error.URLError as exc:
        raise PublishError(f"{method} {url}: {exc.reason}") from exc


@dataclass
class PublishReport:
    uploaded: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


class SharePointPublisher:
    def __init__(self, config: KBConfig, secret: str | None = None, send: Send | None = None):
        settings = config.sharepoint or {}
        missing = [k for k in REQUIRED if not settings.get(k)]
        if missing:
            raise PublishError(f"kb.yaml sharepoint block is missing: {', '.join(missing)}")
        self.config, self.settings = config, settings
        self.secret = (
            secret if secret is not None else os.environ.get("TEAMKB_GRAPH_CLIENT_SECRET", "")
        )
        if not self.secret:
            raise PublishError("set TEAMKB_GRAPH_CLIENT_SECRET (from a secret store)")
        self.send = send or _urllib_send
        self._token: str | None = None

    def _bearer(self) -> str:
        if self._token is None:
            body = urllib.parse.urlencode(
                {
                    "client_id": self.settings["client_id"],
                    "client_secret": self.secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                }
            ).encode()
            url = (
                f"https://login.microsoftonline.com/{self.settings['tenant_id']}/oauth2/v2.0/token"
            )
            status, raw = self.send(
                "POST", url, {"Content-Type": "application/x-www-form-urlencoded"}, body
            )
            if status != 200:
                raise PublishError(f"token request failed ({status}): check the app registration")
            self._token = json.loads(raw)["access_token"]
        return self._token

    def call(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str = "application/json",
    ) -> dict:
        url = path if path.startswith("https://") else GRAPH + path
        for attempt in range(5):
            status, raw = self.send(
                method,
                url,
                {
                    "Authorization": f"Bearer {self._bearer()}",
                    "Content-Type": content_type,
                },
                body,
            )
            if status in (429, 503) and attempt < 4:
                time.sleep(2**attempt)
                continue
            if status >= 400:
                raise PublishError(f"Graph {method} {path} -> {status}")
            return json.loads(raw) if raw else {}
        raise PublishError(f"Graph {method} {path}: still throttled")

    def _drive_id(self) -> str:
        site = self.call("GET", f"/sites/{self.settings['site']}")
        library = self.settings.get("library", "Documents")
        drives = self.call("GET", f"/sites/{site['id']}/drives").get("value", [])
        for drive in drives:
            if drive.get("name") == library:
                return drive["id"]
        raise PublishError(f"library {library!r} not found on {self.settings['site']}")

    def publish(self, prune: bool = False) -> PublishReport:
        folder = self.settings["folder"].strip("/")
        local = sorted(p for p in self.config.publish_path.glob("*") if p.is_file())
        if not local:
            raise PublishError(f"nothing to publish in {self.config.publish_path}: run bundle")
        drive = self._drive_id()
        report = PublishReport()
        for path in local:
            target = urllib.parse.quote(f"{folder}/{path.name}")
            self.call(
                "PUT",
                f"/drives/{drive}/root:/{target}:/content",
                path.read_bytes(),
                "text/plain" if path.suffix == ".txt" else "text/markdown",
            )
            report.uploaded.append(path.name)
        if prune:
            names = {p.name for p in local}
            listing = self.call(
                "GET", f"/drives/{drive}/root:/{urllib.parse.quote(folder)}:/children"
            ).get("value", [])
            for item in listing:
                name = item.get("name", "")
                if "file" in item and name.startswith(self.config.name) and name not in names:
                    self.call("DELETE", f"/drives/{drive}/items/{item['id']}")
                    report.removed.append(name)
        return report
