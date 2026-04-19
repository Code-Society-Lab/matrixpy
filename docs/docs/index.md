# matrix.py

<div align="center">
  <em>A simple, developer-friendly library to create powerful <a href="https://matrix.org">Matrix</a> bots.</em>
</div>

<img alt="image" src="img/matrixpy-white.svg#only-dark" />
<img alt="image" src="img/matrixpy-black.svg#only-light" />

<hr />

[![Static Badge](https://img.shields.io/badge/%F0%9F%93%9A-Documentation-%235c5c5c)](https://github.com/Code-Society-Lab/matrixpy/wiki)
[![Join Discord](https://discordapp.com/api/guilds/823178343943897088/widget.png?style=shield)](https://discord.gg/code-society-823178343943897088)
[![Join Matrix](https://img.shields.io/matrix/codesociety%3Amatrix.org?logo=matrix&label=%20&labelColor=%23202020&color=%23202020)](https://matrix.to/#/%23codesociety:matrix.org )
[![Tests](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml/badge.svg)](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml)
[![CodeQL Advanced](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml/badge.svg)](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Code-Society-Lab/matrixpy/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Code-Society-Lab/matrixpy)

Matrix.py is a lightweight and intuitive Python library to build bots on
the [Matrix protocol](https://matrix.org). It provides a clean,
decorator-based API similar to popular event-driven frameworks, allowing
developers to focus on behavior rather than boilerplate.

#### Key Features

- Minimal setup, easy to extend
- Event-driven API using async/await
- Clean command registration
- Automatic event handler registration
- Built on [matrix-nio](https://github.com/matrix-nio/matrix-nio)

# Quickstart

**Requirements**

- Python 3.10+

```
pip install matrix-python
```

If you plan on contributing to matrix.py, we recommend to install the development libraries:

```
pip install -e .[dev]
```

*Note*: It is recommended to use
a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
when installing python packages.

```python
from matrix import Bot, Context

bot = Bot()


@bot.command("ping")
async def ping(ctx: Context):
    await ctx.reply("Pong!")


bot.start(config="config.yml")
```

[Documentation](https://github.com/Code-Society-Lab/matrixpy/wiki) - [Examples](https://github.com/Code-Society-Lab/matrixpy/tree/main/examples)

# Contributing

We welcome everyone to contribute!

Whether it's fixing bugs, suggesting features, or improving the docs - every bit helps.

- Submit an issue
- Open a pull request
- Or just hop into our [Matrix](https://matrix.to/#/%23codesociety:matrix.org)
  or [Discord](https://discord.gg/code-society-823178343943897088) server and say hi!

If you intend to contribute, please read
the [CONTRIBUTING.md](https://github.com/Code-Society-Lab/matrixpy/blob/main/CONTRIBUTING.md) first. Additionally, *
*every
contributor** is expected to follow
the [code of conduct](https://github.com/Code-Society-Lab/matrixpy/blob/main/CODE_OF_CONDUCT.md).

# License

This project is licensed under the terms
of [MIT license](https://github.com/Code-Society-Lab/matrixpy/blob/main/LICENSE).
