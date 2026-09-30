"""Knowledge-base settings, read from ``kb.yaml`` at the root of a knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_NAME = "kb.yaml"


class ConfigError(ValueError):
    pass


@dataclass
class KBConfig:
    root: Path
    name: str
    tags: list[str]
    classifications: list[str] = field(default_factory=lambda: ["public", "internal", "restricted"])
    publish_ceiling: str = "internal"
    publish_format: str = "txt"
    publish_dir: str = "_published"
    cards_dir: str = "cards"
    review_months: int = 12
    bundle_max_chars: int = 100_000
    summary_max_words: int = 120
    allow_contact_details: bool = False

    @property
    def cards_path(self) -> Path:
        return self.root / self.cards_dir

    @property
    def publish_path(self) -> Path:
        return self.root / self.publish_dir

    def rank(self, classification: str) -> int:
        """Position in the classification order; unknown labels rank as most sensitive."""
        try:
            return self.classifications.index(classification)
        except ValueError:
            return len(self.classifications)


def load_config(root: Path) -> KBConfig:
    path = root / CONFIG_NAME
    if not path.is_file():
        raise ConfigError(f"{path} not found: a knowledge base needs a {CONFIG_NAME} at its root")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must be a mapping of settings")
    if not data.get("name"):
        raise ConfigError(f"{path}: 'name' is required")
    tags = data.get("tags") or []
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ConfigError(f"{path}: 'tags' must be a list of strings (the controlled vocabulary)")

    known = {f for f in KBConfig.__dataclass_fields__ if f not in ("root", "name", "tags")}
    unknown = set(data) - known - {"name", "tags"}
    if unknown:
        raise ConfigError(f"{path}: unknown setting(s): {', '.join(sorted(unknown))}")

    config = KBConfig(root=root, name=str(data["name"]), tags=list(tags))
    for key in known:
        if key in data:
            setattr(config, key, data[key])

    if config.publish_ceiling not in config.classifications:
        raise ConfigError(
            f"{path}: publish_ceiling '{config.publish_ceiling}' is not one of "
            f"{config.classifications}"
        )
    if config.publish_format not in ("txt", "md"):
        raise ConfigError(f"{path}: publish_format must be 'txt' or 'md'")
    return config
