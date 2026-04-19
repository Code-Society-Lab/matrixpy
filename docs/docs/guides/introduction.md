# Introduction
Matrix.py is a simple, developer-friendly Python library designed to help you build powerful bots on the [Matrix protocol](https://matrix.org/). The library provides a clean, event-driven API built around Python's async/await syntax, with easy command registration and handler management so developers can focus on bot behavior instead of boilerplate setup.

Matrix.py is built on top of the popular Matrix client library [matrix-nio](https://github.com/matrix-nio/matrix-nio).

# Prerequisites
Before using Matrixpy, you should have:
- [Python](https://www.python.org/downloads/) 3.10 or higher installed.
- A [Matrix account](https://matrix.org/docs/chat_basics/matrix-for-im/#creating-a-matrix-account) to act as the bot's identity.

# Installation

Matrixpy can be installed easily using pip:

```bash
pip install matrix-python
```

### Creating a Virtual Environment (Recommended)

Before installing Matrix.py, it's strongly recommended to create a virtual environment. This keeps dependencies isolated and avoids conflicts with other Python projects.

1. Create a venv

    ```bash
    python -m venv venv
    ```

2. Activate the venv

    On Linux/macOS:
    ```bash
    source venv/bin/activate
    ```
    
    On Windows (PowerShell):
    ```bash
    venv\Scripts\Activate
    ```

### Installing from Source (For Development)
If you want to work with the latest development version or contribute to Matrix.py, clone the repository:
```bash
git clone https://github.com/Code-Society-Lab/matrixpy.git
cd matrixpy
```

Then install the package with development dependencies:
```bash
pip install -e .[dev]
```

# Basic Configuration

Once installed, you'll need to configure a bot by providing:
- A username (Matrix ID) and password.
- Optionally, a server or homeserver URL if not using the default (matrix.org).

### Configuration with a YAML File (Recommended)

Create a file named config.yaml:
```yaml
USERNAME: "@yourbot:matrix.org"
PASSWORD: "your_password"
```

Then load it when creating your bot instance:
```python
from matrix import Bot

bot = Bot(config="config.yaml")
```

!!! NOTE
    For full details on available config options and examples, see the [Configuration](configuration.md) guide and the [`Config`](../reference/config.md) reference.

# Core Concepts
Matrix.py bots are built around two simple ideas:
- Events: things that happen in a Matrix room
- Commands: messages your bot reacts to on purpose

### Handling Events
Matrix is an event-based system: messages, joins, reactions, and more are all delivered as events.

Matrix.py allows you to listen to these events using the `@bot.event` decorator.

For example, to react whenever a message is sent:
```python
from matrix import Bot, Context
from matrix.bot import MatrixRoom, RoomMessageText 

bot = Bot()


@bot.event
async def on_message(matrix_room: MatrixRoom, event: RoomMessageText):
    print(f"Message received from {event.sender}: {event.body}")


bot.start(config="config.yaml")
```

### Registering Commands
Commands are a type of message handler that only trigger when a user sends a message starting with the bot's prefix (default "!"). They simplify building interactive bot features.

```python
from matrix import Context


@bot.command()
async def ping(ctx: Context):
    await ctx.send("Pong!")
```

Now, when a user sends `!ping` the bot will answer `Pong!`.


Commands can accept arguments, which are automatically parsed from the user's message:
```python
@bot.command()
async def say(ctx: Context, *, text: str):
    await ctx.send(text)
```

!!! warning
    Bots do not support encrypted rooms yet.
