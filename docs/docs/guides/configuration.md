# Configuration

The [`Config`](../reference/config.md) class is the central configuration handler used by Matrix.py. It manages all settings required to connect and authenticate with a Matrix homeserver, including:
- Homeserver URL
- Username (Matrix ID)
- Authentication (password or access token)
- Command prefix
- Loading settings from a YAML file

This documentation explains how to use `Config` in your bot project.

### Overview

Matrix.py's `Config` allows you to configure your bot in two ways:
- Via a YAML configuration file (recommended)
- Manually through constructor parameters

If a YAML file is provided, it loads values from that file. Otherwise, configuration values can be passed directly. At least one authentication method, either password or token, must be provided.

!!! WARNING
    If neither PASSWORD nor TOKEN is supplied (either via the YAML file or via parameters), the bot will fail to log in and will raise a [`ConfigError`](../reference/errors.md).

# Configuration Options
- `HOMESERVER` — Matrix homeserver URL (default: https://matrix.org).
- `USERNAME` — Your bot's Matrix HumID (required).
- `PASSWORD` — Password for your bot account (required unless TOKEN is provided).
- `TOKEN` — Matrix access token (optional alternative to password).
- `PREFIX` — Command prefix for bot commands (default: !).

# Usage Examples
### Load From YAML

```python
bot.start(config="config.yaml")
```
This method loads the configuration from the YAML file and initializes the bot with those settings.

### Manual Configuration

You can also configure the bot programmatically without a YAML file:

```python
bot.start(
    config=Config(
        homeserver="https://matrix.org",
        username="@yourbot:matrix.org",
        password="your_password",
        prefix="!"
    )
)
```
This is useful for dynamic setups or scripts where configuration files aren't necessary.

# Behavior and Defaults
- If a configuration file path is passed, `Config` will load settings from that file.
- If no file is provided, values passed via constructor parameters (username, password, etc.) are used.
- The default homeserver URL is https://matrix.org if none is specified.
- A command prefix is always set, either via YAML or defaulting to "!".

# Environment Variables

### Overview
Matrix.py supports environment variable substitution in YAML configuration files using the ${VAR_NAME} syntax. This feature is powered by [EnvYAML](https://pypi.org/project/envyaml/), which allows you to keep sensitive information (like passwords and tokens) out of your repository and manage configuration across different environments.

### Usage
When loading a configuration from a YAML file, you can reference environment variables using the ${VARIABLE_NAME} syntax:
```yaml
HOMESERVER: https://matrix.org
USERNAME: @yourbot:matrix.org
PASSWORD: ${BOT_PASSWORD}
TOKEN: ${BOT_TOKEN}
PREFIX: !
```
When the config file is loaded, EnvYAML will automatically substitute ${BOT_PASSWORD} and ${BOT_TOKEN} with the corresponding environment variable values.

### Example
```yaml
HOMESERVER: ${MATRIX_HOMESERVER:-https://matrix.org}
USERNAME: ${MATRIX_USERNAME}
PASSWORD: ${MATRIX_PASSWORD}
PREFIX: !

custom_section:
  api_key: ${API_KEY}
  debug_mode: ${DEBUG_MODE:-false}
```
