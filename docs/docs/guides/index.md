# Welcome to **Matrix.py**
Matrix.py is a lightweight and intuitive Python library for building bots on the [Matrix protocol](https://matrix.org). It provides a clean, decorator-based API similar to popular event-driven frameworks, allowing developers to focus on behavior rather than boilerplate.

#### Key Features
- Minimal setup, easy to extend
- Event-driven API using async/await
- Clean command registration
- Automatic event handler registration
- Built on [matrix-nio](https://github.com/matrix-nio/matrix-nio)

# Quick Start
Here's a minimal example to get your bot running. For a more detailed guide, see the [Introduction](introduction.md).

### Install and Configure

Install Matrix.py:
```
pip install matrix-python
```

Create a `config.yaml`:
```yaml
USERNAME: "@yourbot:matrix.org"
PASSWORD: "your_password"
```

### Create the Bot
```python
from matrix import Bot, Context, Config

bot = Bot()
```

### Handle Event
React to all messages in rooms:
```python
@bot.event
async def on_message(room, event):
    print(f"[{room.room_id}] {event.sender}: {event.body}")
```
This will log every message to the console.

### Register Commands
Commands are triggered by messages starting with your prefix (default "!"):
```python
# Respond to !ping
@bot.command()
async def ping(ctx: Context):
    await ctx.send("Pong!")

# Respond to !say <text>
@bot.command()
async def say(ctx: Context, *, text: str):
    await ctx.send(text)
```
- Commands automatically parse arguments from messages.
- The command name defaults to the function name but can be customized.

### Run the Bot
```python
bot.start(config="config.yaml")

# or

bot.start(config=Config(
    username="...",
    password="..."
))
```
- Now your bot will:
- Log all messages
- Reply to `!ping` with `Pong!` 
- Echo messages with `!say <text>`

# Resources
Here's a list of resources that might be useful when working with **matrix.py**:
- [Python's Doc](https://docs.python.org/3/)
- [matrix-nio](https://github.com/matrix-nio/matrix-nio)
- [Matrix Protocol](https://matrix.org/docs/chat_basics/matrix-for-im/)

# Contributing
We any contributions, whether it's fixing bugs, suggesting features, or improving the docs, every bit helps:
- [Submit an issue](https://github.com/Code-Society-Lab/matrixpy/issues)
- [Open a pull request](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project)
- Or hop into our [Matrix](https://matrix.to/#/#codesociety:matrix.org) or [Discord community](https://discord.gg/code-society-823178343943897088) and say hi!

If you intend to contribute, please read the [CONTRIBUTING.md](https://github.com/Code-Society-Lab/matrixpy/blob/main/CONTRIBUTING.md) first. Additionally, **every contributor** is expected to follow the [code of conduct](https://github.com/Code-Society-Lab/matrixpy/blob/main/CODE_OF_CONDUCT.md).
