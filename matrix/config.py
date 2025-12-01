import yaml
from .errors import ConfigError
from typing import Optional


class Config:
    """
    Configuration handler for Matrix client settings. Including the following:

        homeserver: Defaults to 'https://matrix.org'
        user_id: The Matrix user ID (username).
        password: (Optional) One of the password or token must be provided.
        token: (Optional) One of the password or token must be provided.
        prefix: Defaults to '!' if not specified in the config file.

    :param config_path: Path to the YAML configuration file.
    :param homeserver: The Matrix homeserver URL.
    :param username: The Matrix user ID (username).
    :param password: The password for the Matrix user.
    :param token: The access token for the Matrix user.
    :param prefix: The command prefix.

    :raises FileNotFoundError: If the configuration file does not exist.
    :raises yaml.YAMLError: If the configuration file cannot be parsed.
    :raises ConfigError: If neither password or token has been provided.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        *,
        homeserver: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> None:
        self.homeserver: str = homeserver or "https://matrix.org"
        self.user_id: Optional[str] = username
        self.password: Optional[str] = password
        self.token: Optional[str] = token
        self.prefix: str = prefix or "!"

        if config_path:
            self.load_from_file(config_path)
        elif not (self.password or self.token):
            raise ConfigError("username and password or token")

    def load_from_file(self, config_path: str) -> None:
        """Load Matrix client settings via YAML config file."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

            if not (config.get("PASSWORD") or config.get("TOKEN")):
                raise ConfigError("USERNAME and PASSWORD or TOKEN")

            self.homeserver = config.get("HOMESERVER", "https://matrix.org")
            self.user_id = config.get("USERNAME")
            self.password = config.get("PASSWORD", None)
            self.token = config.get("TOKEN", None)
            self.prefix = config.get("PREFIX", "!")
