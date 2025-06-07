import pytest
from matrix.errors import ConfigError
from matrix.config import Config


def test_config_defaults_success():
    cfg = Config(username="grace", password="secret")
    assert cfg.homeserver == "https://matrix.org"
    assert cfg.user_id == "grace"
    assert cfg.password == "secret"
    assert cfg.token is None
    assert cfg.prefix == "!"


def test_load_from_file_success():
    cfg = Config("tests/config/sample_config_files/config_file_succes.yaml")
    assert cfg.homeserver == "https://matrix.org"
    assert cfg.user_id == "@grace:matrix.org"
    assert cfg.password == "grace1234"
    assert cfg.prefix == "!"


def test_raise_configerror_from_arguments():
    with pytest.raises(ConfigError) as exc:
        Config(username="missingpassword")
    assert "username and password or token" in str(exc.value)


def test_raise_configerror_from_file():
    with pytest.raises(ConfigError) as exc:
        Config("tests/config/sample_config_files/config_file_error.yaml")
    assert "USERNAME and PASSWORD or TOKEN" in str(exc.value)
