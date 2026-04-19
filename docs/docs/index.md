<div align="center" style="margin-bottom: 20px">
  <em>A simple, developer-friendly library to create powerful <a href="https://matrix.org">Matrix</a> bots.</em>
</div>

<div align="center">
  <img alt="matrix.py logo" src="img/matrixpy-white.svg#only-dark"/>
  <img alt="matrix.py logo" src="img/matrixpy-black.svg#only-light" />
</div>

<div align="center" markdown>

[Get Started](guides/introduction.md){ .md-button .md-button--primary }
[Reference](reference/bot.md){ .md-button }

</div>

<div align="center">

<p>
  <a href="https://discord.gg/code-society-823178343943897088">
    <img
      src="https://discordapp.com/api/guilds/823178343943897088/widget.png?style=shield"
      alt="Join Discord"
    />
  </a>

  <a href="https://matrix.to/#/%23codesociety:matrix.org">
    <img
      src="https://img.shields.io/matrix/codesociety%3Amatrix.org?logo=matrix&label=%20&labelColor=%23202020&color=%23202020"
      alt="Join Matrix"
    />
  </a>

  <a href="https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml">
    <img
      src="https://github.com/Code-Society-Lab/matrixpy/actions/workflows/tests.yml/badge.svg"
      alt="Tests"
    />
  </a>

  <a href="https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml">
    <img
      src="https://github.com/Code-Society-Lab/matrixpy/actions/workflows/codeql.yml/badge.svg"
      alt="CodeQL Advanced"
    />
  </a>

  <a href="https://securityscorecards.dev/viewer/?uri=github.com/Code-Society-Lab/matrixpy">
    <img
      src="https://api.securityscorecards.dev/projects/github.com/Code-Society-Lab/matrixpy/badge"
      alt="OpenSSF Scorecard"
    />
  </a>
</p>

</div>
---

Matrix.py is a lightweight and intuitive Python library to build bots on the [Matrix protocol](https://matrix.org). It provides a clean, decorator-based API similar to popular event-driven frameworks, allowing developers to focus on behavior rather than boilerplate.

- **Minimal setup** — install and have a working bot running in minutes
- **Event-driven** — async/await API reacting to any Matrix room event
- **Command system** — decorator-based commands with automatic argument parsing
- **Extensions** — split your bot into modules as it grows

## Quickstart

=== "Install"

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

=== "Configure"

    Create a `config.yml` file:

    ```yaml
    USERNAME: "@yourbot:matrix.org"
    PASSWORD: "your_password"
    ```

    Or use environment variables:

    ```yaml
    USERNAME: ${MATRIX_USERNAME}
    PASSWORD: ${MATRIX_PASSWORD}
    ```

=== "Code"

    ```python
    from matrix import Bot, Context

    bot = Bot()


    @bot.command("ping")
    async def ping(ctx: Context):
        await ctx.reply("Pong!")


    bot.start(config="config.yml")
    ```

    Send `!ping` in any room the bot is in — it will reply `Pong!`.

## Where to go next

<div class="grid cards" markdown>

-   :fontawesome-solid-book-open: **Guides**

    ---

    Step-by-step tutorials covering commands, events, checks, extensions, and more.

    [:octicons-arrow-right-24: Start with the Introduction](guides/introduction.md)

-   :fontawesome-solid-code: **Reference**

    ---

    Complete API documentation for every class and function in the library.

    [:octicons-arrow-right-24: Browse the Reference](reference/bot.md)

-   :fontawesome-solid-terminal: **Examples**

    ---

    Ready-to-run example bots demonstrating common patterns and use cases.

    [:octicons-arrow-right-24: View Examples](/examples)

-   :fontawesome-brands-github: **Source Code**

    ---

    Browse the source, open issues, and contribute on GitHub.

    [:octicons-arrow-right-24: View on GitHub](https://github.com/Code-Society-Lab/matrixpy)

</div>

## Contributing

We welcome everyone to contribute! Whether it's fixing bugs, suggesting features, or improving the docs — every bit helps.

- [Submit an issue](https://github.com/Code-Society-Lab/matrixpy/issues)
- [Open a pull request](https://github.com/Code-Society-Lab/matrixpy/blob/main/CONTRIBUTING.md)
- Hop into our [Matrix](https://matrix.to/#/%23codesociety:matrix.org) or [Discord](https://discord.gg/code-society-823178343943897088) and say hi!

Please read the [CONTRIBUTING.md](https://github.com/Code-Society-Lab/matrixpy/blob/main/CONTRIBUTING.md) and follow the [code of conduct](https://github.com/Code-Society-Lab/matrixpy/blob/main/CODE_OF_CONDUCT.md).

## License

Released under the [MIT License](https://github.com/Code-Society-Lab/matrixpy/blob/main/LICENSE).
