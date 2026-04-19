# Ping Bot

The simplest possible bot — one command that replies to `!ping` with `Pong!`. Start here if you're new to matrix.py.

```python
--8<-- "examples/ping.py"
```

`ctx.reply()` sends a message back to the same room the command was received in. Swap `"Pong!"` for any string, including formatted text.
