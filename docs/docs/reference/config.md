# Config

`Config` holds all settings needed to connect and authenticate with a Matrix homeserver. It can be loaded from a YAML file or constructed directly with keyword arguments. At minimum, a homeserver URL and one authentication method (password or access token) are required.

```python
from matrix.config import Config

# Load from a YAML file
config = Config(config_path="config.yml")

# Or configure manually
config = Config(
    homeserver="https://matrix.org",
    username="@mybot:matrix.org",
    password="hunter2",
)
```

::: matrix.config.Config
