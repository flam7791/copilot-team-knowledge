import pytest

from teamkb.config import ConfigError, load_config


def test_example_config(config):
    assert config.name == "Harbour Data Team"
    assert config.publish_ceiling == "internal"
    assert config.rank("public") < config.rank("internal") < config.rank("restricted")


def test_unknown_classification_ranks_highest(config):
    assert config.rank("unheard-of") > config.rank("restricted")


def test_missing_config(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_unknown_setting(kb):
    (kb / "kb.yaml").write_text("name: X\ntags: [a]\npublish_celing: internal\n")
    with pytest.raises(ConfigError, match="unknown setting"):
        load_config(kb)


def test_ceiling_must_be_a_known_classification(kb):
    (kb / "kb.yaml").write_text("name: X\ntags: [a]\npublish_ceiling: top\n")
    with pytest.raises(ConfigError, match="publish_ceiling"):
        load_config(kb)


def test_format_must_be_txt_or_md(kb):
    (kb / "kb.yaml").write_text("name: X\ntags: [a]\npublish_format: docx\n")
    with pytest.raises(ConfigError, match="publish_format"):
        load_config(kb)
