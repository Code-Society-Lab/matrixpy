import pytest
from matrix.errors import ConfigError
from matrix.config import Config


def test_config_defaults():
    cfg = Config(username="grace", password="secret")
    assert cfg.homeserver == "https://matrix.org"
    assert cfg.user_id == "grace"
    assert cfg.password == "secret"
    assert cfg.token is None
    assert cfg.prefix == "!"


def test_config_without_password_or_token():
    with pytest.raises(ConfigError) as exc:
        Config(username="missingpassword")
    assert "username and password or token" in str(exc.value)


def test_load_from_file():
    cfg = Config(config_path="tests/config/config_file.yaml")
    assert cfg.homeserver == "https://matrix.org"
    assert cfg.user_id == "grace"
    assert cfg.password == "grace1234"
    assert cfg.prefix == "!"
