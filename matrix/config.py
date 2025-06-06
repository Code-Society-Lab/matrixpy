import yaml
from matrix.errors import ConfigError
from typing import Optional


class Config:
    """
    Configuration handler for Matrix client settings. Including the following:

        homeserver: Defaults to 'https://matrix.org'
        user_id: The Matrix user ID (username).
        password: (Optional) One of the password or token must be provided.
        token: (Optional) One of the password or token must be provided.
        prefix: Defaults to '!' if not specified in the config file.

    :param config_path: (Optional) Path to the YAML configuration file.
    :type config_path: str

    :param **kwargs: (Optional) Varaiable to Matrix client configuration.
    :type **kwargs: dict[str, Any]

    :raises FileNotFoundError: If the configuration file does not exist.
    :raises yaml.YAMLError: If the configuration file cannot be parsed.
    :raises ConfigError: If neither password or token has been provided.
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        self.homeserver: str = kwargs.get("homeserver", "https://matrix.org")
        self.user_id: Optional[str] = kwargs.get("username")
        self.password: Optional[str] = kwargs.get("password", None)
        self.token: Optional[str] = kwargs.get("token", None)
        self.prefix: str = kwargs.get("prefix", "!")

        if config_path:
            self.load_from_file(config_path)
        elif not (self.password or self.token):
            raise ConfigError("username and password or token")

    def load_from_file(self, config_path: str):
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
