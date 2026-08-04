# Component

Components are reusable message elements that can render content in both plain text and HTML. Subclasses implement `to_plain_text` and `render`, and can then be passed to methods such as `Context.reply`. matrix.py includes a built-in Table component for displaying labeled fields in a configurable column layout.

```python
from matrix import Bot, Table

bot = Bot()


@bot.command()
async def weather(ctx):
    weather = Table(title="Los Angeles")

    weather.add_field("Description", "Clear Sky")
    weather.add_field("Visibility", "10000m | 32808ft")
    weather.add_field("Temperature", "71.33°F | 21.85°C")
    weather.add_field("Feels Like", "71.33°F | 21.85°C")
    weather.add_field("Atmospheric Pressure", "1012 hPa")
    weather.add_field("Humidity", "66%")

    await ctx.reply(component=weather)
```

::: matrix.component.Component
