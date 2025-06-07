import pytest
import yaml

from matrix.errors import ConfigError
from matrix.config import Config


@pytest.fixture
def config_default():
    return Config(username="grace", password="secret")


@pytest.mark.parametrize(
    "attr,expected",
    [
        ("homeserver", "https://matrix.org"),
        ("user_id", "grace"),
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

    assert cfg.user_id == "@grace:matrix.org"
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
    yaml_text = "HOMESERVER: https://matrix.org"
    file = tmp_path / "err.yaml"
    file.write_text(yaml_text)
    with pytest.raises(ConfigError) as exc:
        Config(str(file))
    # the assert make sure that the error is raised from
    # the load_from_file method and not the constructor
    assert "USERNAME and PASSWORD or TOKEN" in str(exc.value)


def test_token_only():
    token = "my_very_secure_token"
    cfg = Config(token=token)

    assert cfg.token == token
    assert cfg.password is None
    assert cfg.homeserver == "https://matrix.org"
