# matrix.py
> A simple, developer-friendly library to create powerful [Matrix](https://matrix.org) bots.

[![Static Badge](https://img.shields.io/badge/%F0%9F%93%9A-Documentation-%235c5c5c)](https://github.com/Code-Society-Lab/matrixpy/wiki)
[![Join on Discord](https://discordapp.com/api/guilds/823178343943897088/widget.png?style=shield)](https://discord.gg/code-society-823178343943897088)
[![Tests](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml/badge.svg)](https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml)

matrix.py is a lightweight and intuitive Python library to build bots on
the [Matrix protocol]([Matrix](https://matrix.org)). It provides a clean,
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
pip install git+ssh://git@github.com:Code-Society-Lab/matrixpy.git
```

If you plan on contributing to matrix.py, we recommend to install the development libraries:
```
pip install .[env]
```

*Note*: It is recommended to use a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) when installing python packages.


```python
from matrix import Bot, Context

bot = Bot(username="@gracehopper:matrix.org", password="grace1234")


@bot.command("ping")
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.send("Pong!")


bot.start()
```

[Documentation](https://github.com/Code-Society-Lab/matrixpy/wiki) - [Examples]([https://github.com/Code-Society-Lab/matrixpy/wiki](https://github.com/Code-Society-Lab/matrixpy/tree/main/examples))

# Contributing
We welcome everyone to contribute! 

Whether it's fixing bugs, suggesting features, or improving the docs - every bit helps.
- Submit an issue
- Open a pull request
- Or just hop into our [Discord community](https://discord.gg/code-society-823178343943897088) and say hi!

If you intend to contribute, please read the [CONTRIBUTING.md](./CONTRIBUTING.md) first. Additionally, **every contributor** is expected to follow the [code of conduct](./CODE_OF_CONDUCT.md).

# License
matrix.py is released under [GPL-3.0](https://opensource.org/license/gpl-3-0)
