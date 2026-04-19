<div align="center">
  <em>A simple, developer-friendly library to create powerful <a href="https://matrix.org">Matrix</a> bots.</em>
</div>

<div align="center">
  <img alt="matrix.py" src="https://github.com/user-attachments/assets/d9140a9e-27fa-44e4-a5ca-87ee7bbf868f" />
</div>

<div align="center">

[<img src="https://img.shields.io/badge/Get%20Started-black?style=for-the-badge" />](https://matrixpy.code-society.xyz/guides/introduction/)
[<img src="https://img.shields.io/badge/Reference-555555?style=for-the-badge" />](https://matrixpy.code-society.xyz/reference/bot/)

</div>

<div align="center">

[![Join Discord](https://discordapp.com/api/guilds/823178343943897088/widget.png?style=shield)](https://discord.gg/code-society-823178343943897088)
[![Join Matrix](https://img.shields.io/matrix/codesociety%3Amatrix.org?logo=matrix&label=%20&labelColor=%23202020&color=%23202020)](https://matrix.to/#/%23codesociety:matrix.org)
[![Tests](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml/badge.svg)](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml)
[![CodeQL Advanced](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml/badge.svg)](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Code-Society-Lab/matrixpy/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Code-Society-Lab/matrixpy)

</div>

---

Matrix.py is a lightweight and intuitive Python library to build bots on the [Matrix protocol](https://matrix.org). It
provides a clean, decorator-based API similar to popular event-driven frameworks, allowing developers to focus on
behavior rather than boilerplate.

- **Minimal setup** — install and have a working bot running in minutes
- **Event-driven** — async/await API reacting to any Matrix room event
- **Command system** — decorator-based commands with automatic argument parsing
- **Extensions** — split your bot into modules as it grows

## Quickstart

**Requirements:** Python 3.10+

```bash
pip install matrix-python
```

Using a virtual environment is strongly recommended:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install matrix-python
```

Create a `config.yml`:

```yaml
USERNAME: "@yourbot:matrix.org"
PASSWORD: "your_password"
```

```python
from matrix import Bot, Context

bot = Bot()


@bot.command("ping")
async def ping(ctx: Context):
    await ctx.reply("Pong!")


bot.start(config="config.yml")
```

Send `!ping` in any room the bot is in, it will reply `Pong!`.

## Where to go next

- [**Guides**](https://matrixpy.code-society.xyz/guides/introduction/) — step-by-step tutorials covering commands,
  events, checks, extensions, and more
- [**Reference**](https://matrixpy.code-society.xyz/reference/bot/) — complete API documentation for every class and
  function
- [**Examples**](https://github.com/Code-Society-Lab/matrixpy/tree/main/examples) — ready-to-run example bots
  demonstrating common patterns

## Contributing

We welcome everyone to contribute! Whether it's fixing bugs, suggesting features, or improving the docs. Every bit
helps.

- [Submit an issue](https://github.com/Code-Society-Lab/matrixpy/issues)
- [Open a pull request](https://github.com/Code-Society-Lab/matrixpy/blob/main/CONTRIBUTING.md)
- Hop into our [Matrix](https://matrix.to/#/%23codesociety:matrix.org)
  or [Discord](https://discord.gg/code-society-823178343943897088) and say hi!

Please read the [CONTRIBUTING.md](./CONTRIBUTING.md) and follow the [code of conduct](./CODE_OF_CONDUCT.md).

## License

Released under the [MIT License](https://github.com/Code-Society-Lab/matrixpy/blob/main/LICENSE).
