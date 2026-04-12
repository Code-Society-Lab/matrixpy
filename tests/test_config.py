import os
from unittest.mock import patch

import pytest
import yaml

from matrix.config import Config
from matrix.errors import ConfigError


@pytest.fixture
def config_default():
    return Config(username="grace", password="secret")


@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "test.yaml"
    config.write_text(
        "USERNAME: '@bot:matrix.org'\n"
        "PASSWORD: 'secret'\n"
        "PREFIX: '!'\n"
        "LOG_LEVEL: 'INFO'\n"
        "bot:\n"
        "  main_channel: '!abc123:matrix.org'\n"
    )
    return config


@pytest.fixture
def config(config_file):
    return Config(config_path=str(config_file))


def test_get__returns_top_level_value(config: Config) -> None:
    assert config.get(key="LOG_LEVEL") == "INFO"


def test_get__returns_none_when_key_missing_and_no_default(config: Config) -> None:
    assert config.get(key="MISSING") is None


def test_get__returns_default_when_key_missing(config: Config) -> None:
    assert config.get(key="MISSING", default="fallback") == "fallback"


def test_get__returns_section_value(config: Config) -> None:
    assert config.get(key="main_channel", section="bot") == "!abc123:matrix.org"


def test_get__returns_default_when_section_missing(config: Config) -> None:
    assert (
        config.get(key="main_channel", section="MISSING", default="fallback")
        == "fallback"
    )


def test_get__returns_default_when_section_key_missing(config: Config) -> None:
    assert config.get(key="MISSING", section="bot", default="fallback") == "fallback"


def test_getitem__returns_value(config: Config) -> None:
    assert config["LOG_LEVEL"] == "INFO"


def test_getitem__raises_key_error_when_missing(config: Config) -> None:
    with pytest.raises(KeyError):
        _ = config["MISSING"]


@pytest.mark.parametrize(
    "attr,expected",
    [
        ("homeserver", "https://matrix.org"),
        ("username", "grace"),
        ("password", "secret"),
        ("token", None),
        ("prefix", "!"),
    ],
)
def test_config_defaults_success(config_default, attr, expected):
    assert getattr(config_default, attr) == expected


def test_loading_valid_yaml(tmp_path):
    yaml_text = """
    HOMESERVER: https://matrix.org
    USERNAME:   "@grace:matrix.org"
    PASSWORD:    grace1234
    PREFIX:     "/"
    """
    config_file = tmp_path / "good.yaml"
    config_file.write_text(yaml_text)

    cfg = Config(str(config_file))

    assert cfg.username == "@grace:matrix.org"
    assert cfg.password == "grace1234"
    assert cfg.prefix == "/"


def test_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        Config(str(tmp_path / "nope.yaml"))


def test_bad_yaml_syntax(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: : yaml")
    with pytest.raises(yaml.YAMLError):
        Config(str(bad))


def test_missing_credentials_raises_ConfigError_kwargs():
    with pytest.raises(ConfigError) as exc:
        Config(username="only_user")
    # the assert make sure that the error is raised from
    # the constructor and not load_from_file method
    assert "username and password or token" in str(exc.value)


def test_missing_credentials_raises_ConfigError_yaml(tmp_path):
    yaml_text = "HOMESERVER: https://matrix.org\n" "PASSWORD: \n" "TOKEN: \n"
    file = tmp_path / "err.yaml"
    file.write_text(yaml_text)

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigError) as exc:
            Config(config_path=str(file))
        assert "USERNAME and PASSWORD or TOKEN" in str(exc.value)


def test_token_only():
    token = "my_very_secure_token"
    cfg = Config(token=token)

    assert cfg.token == token
    assert cfg.password is None
    assert cfg.homeserver == "https://matrix.org"
