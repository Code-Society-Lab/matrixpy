from typing import Any

from envyaml import EnvYAML

from .errors import ConfigError


class Config:
    """Configuration handler for Matrix client settings.

    Manages all settings required to connect and authenticate with a Matrix
    homeserver. Configuration can be loaded from a YAML file or provided
    directly via constructor parameters. At least one authentication method
    must be provided.

    # Example

    ```python
    # Load from file
    config = Config(config_path="path/to/config..yaml")

    # Manual configuration
    config = Config(username="@bot:matrix.org", password="secret")
    ```
    """

    def __init__(
        self,
        config_path: str | None = None,
        *,
        homeserver: str | None = None,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        prefix: str | None = None,
    ) -> None:
        """Initialize the bot configuration.

        Loads configuration from a YAML file if provided, otherwise uses
        the provided parameters directly. At least one of password or token
        must be supplied.

        # Example

        ```python
        config = Config(
            username="@bot:matrix.org",
            password="secret",
            prefix="!",
        )
        ```
        """
        self._data: dict[str, Any] = {}

        self.homeserver: str = homeserver or "https://matrix.org"
        self.username: str | None = username
        self.password: str | None = password
        self.token: str | None = token
        self.prefix: str = prefix or "!"

        if config_path:
            self.load_from_file(config_path)
        else:
            if not self.password and not self.token:
                raise ConfigError("username and password or token")

            self._data = {
                "HOMESERVER": self.homeserver,
                "USERNAME": self.username,
                "PASSWORD": self.password,
                "TOKEN": self.token,
                "PREFIX": self.prefix,
            }

    def load_from_file(self, config_path: str) -> None:
        """Load Matrix client settings from a YAML config file.

        Supports environment variable substitution via EnvYAML. Values in
        the YAML file can reference environment variables using ${VAR} syntax.

        # Example

        ```python
        config = Config()
        config.load_from_file("path/to/config.yaml")
        ```
        """
        self._data = dict(EnvYAML(config_path))

        password = self._data.get("PASSWORD", None)
        token = self._data.get("TOKEN", None)

        if not password and not token:
            raise ConfigError("USERNAME and PASSWORD or TOKEN")

        self.homeserver = self._data.get("HOMESERVER", "https://matrix.org")
        self.username = self._data.get("USERNAME")
        self.password = password
        self.token = token
        self.prefix = self._data.get("PREFIX", "!")

    def get(self, key: str, *, section: str | None = None, default: Any = None) -> Any:
        """Access a config value by key, optionally scoped to a section.

        # Example

        ```python
        config.get(key="main_channel", section="bot")
        config.get(key="log_level", default="INFO")
        ```
        """
        if section in self._data:
            return self._data.get(section, {}).get(key, default)
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Access a config value by key, raising KeyError if not found.

        # Example

        ```python
        config["bot"]["main_channel"]
        ```
        """
        return self._data[key]
