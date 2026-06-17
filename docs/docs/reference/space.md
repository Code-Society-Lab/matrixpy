# Space

`Space` extends `Room` to represent a Matrix Space. It is returned by `Bot.get_space()` and `Bot.get_spaces()` instead of a plain `Room` whenever the room type is `m.space`.

```python
from matrix import Bot

bot = Bot()

space = bot.get_space("!space123:matrix.org")
if space:
    print(space.name)
```

::: matrix.space.Space
