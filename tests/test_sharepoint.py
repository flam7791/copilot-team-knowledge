"""Publishing to SharePoint through a simulated Microsoft Graph."""

import json
import shutil
from pathlib import Path

import pytest

from teamkb.config import load_config
from teamkb.sharepoint import PublishError, SharePointPublisher

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "harbour-data-team"
SETTINGS = {
    "tenant_id": "t",
    "client_id": "c",
    "site": "contoso.sharepoint.com:/sites/team",
    "library": "Documents",
    "folder": "Team KB/_published",
}


class FakeGraph:
    def __init__(self, remote=()):
        self.remote = {name: f"id-{i}" for i, name in enumerate(remote)}
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url))
        if "login.microsoftonline.com" in url:
            assert b"grant_type=client_credentials" in body
            return 200, json.dumps({"access_token": "tok"}).encode()
        assert headers["Authorization"] == "Bearer tok"
        if url.endswith("/sites/contoso.sharepoint.com:/sites/team"):
            return 200, b'{"id": "site-1"}'
        if url.endswith("/sites/site-1/drives"):
            return 200, b'{"value": [{"id": "drive-1", "name": "Documents"}]}'
        if method == "PUT":
            name = url.split("/")[-1].split(":")[0]
            self.remote[name] = "new"
            return 201, b"{}"
        if url.endswith(":/children"):
            items = [
                {"id": i, "name": __import__("urllib.parse").parse.unquote(n), "file": {}}
                for n, i in self.remote.items()
            ]
            return 200, json.dumps({"value": items}).encode()
        if method == "DELETE":
            return 204, b""
        return 404, b""


@pytest.fixture
def kb(tmp_path):
    root = tmp_path / "kb"
    shutil.copytree(EXAMPLE, root)
    config = load_config(root)
    config.sharepoint = dict(SETTINGS)
    return config


def test_uploads_only_the_publish_folder(kb):
    graph = FakeGraph()
    report = SharePointPublisher(kb, secret="s", send=graph).publish()
    local = sorted(p.name for p in kb.publish_path.iterdir() if p.is_file())
    assert report.uploaded == local
    puts = [u for m, u in graph.calls if m == "PUT"]
    assert all("Team%20KB/_published/" in u for u in puts)
    assert not any("cards" in u for u in puts)


def test_prune_removes_only_this_kbs_stale_bundles(kb):
    stale = "Harbour Data Team - Old type.txt"
    graph = FakeGraph(remote=[stale, "Someone else's file.docx"])
    report = SharePointPublisher(kb, secret="s", send=graph).publish(prune=True)
    assert report.removed == [stale]
    assert sum(m == "DELETE" for m, _ in graph.calls) == 1


def test_missing_settings_and_secret(kb, monkeypatch):
    kb.sharepoint = {"site": "x:/sites/y"}
    with pytest.raises(PublishError, match="missing"):
        SharePointPublisher(kb, secret="s")
    kb.sharepoint = dict(SETTINGS)
    monkeypatch.delenv("TEAMKB_GRAPH_CLIENT_SECRET", raising=False)
    with pytest.raises(PublishError, match="TEAMKB_GRAPH_CLIENT_SECRET"):
        SharePointPublisher(kb)


def test_kb_yaml_accepts_a_sharepoint_block(tmp_path):
    root = tmp_path / "kb"
    shutil.copytree(EXAMPLE, root)
    text = (root / "kb.yaml").read_text()
    (root / "kb.yaml").write_text(
        text + "\nsharepoint:\n  site: contoso.sharepoint.com:/sites/team\n"
    )
    assert load_config(root).sharepoint["site"].endswith("/sites/team")
