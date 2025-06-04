import yaml


class Config:
    """
    Configuration handler for Matrix client settings. Including the following:

        homeserver: Defaults to 'https://matrix.org'
        user_id: The Matrix user ID (username).
        password: (Optional) One of the password or token must be provided.
        token: (Optional) One of the password or token must be provided.
        prefix: Defaults to '!' if not specified in the config file.

    :param config_file: Path to the YAML configuration file.
    :type config_file: str

    :raises FileNotFoundError: If the configuration file does not exist.
    :raises yaml.YAMLError: If the configuration file cannot be parsed.
    """

    def __init__(self, config_file: str) -> None:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            self.homeserver: str = config.get("SERVER", "https://matrix.org")
            self.user_id: str = config.get("USERNAME")
            self.password: str | None = config.get("PASSWORD", None)
            self.token: str | None = config.get("TOKEN", None)
            self.prefix: str = config.get("PREFIX", "!")
