# Types

Lightweight dataclasses used as parameter and return types throughout the library. `File`, `Image`, `Audio`, and `Video` describe local media you want to upload; `Reaction` represents an emoji reaction event.

```python
from matrix.types import Image

avatar = Image(
    path="/tmp/avatar.png",
    filename="avatar.png",
    mimetype="image/png",
    height=128,
    width=128,
)
await ctx.room.send_image(avatar)
```

::: matrix.types.File

::: matrix.types.Image

::: matrix.types.Audio

::: matrix.types.Video

::: matrix.types.Reaction
