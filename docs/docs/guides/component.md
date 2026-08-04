# What is a Component?

A component is a reusable message element that supplies both the plain-text body and
the formatted HTML body of a message:

* `to_plain_text()` returns the plain-text version.
* `render()` returns the HTML version.

Pass a component to `Context.reply` or `Room.send` with the `component` keyword:

```python
await ctx.reply(component=table)
# Equivalent when sending directly through a room:
await ctx.room.send(component=table)
```

See also the [`Component`](../reference/component.md) reference.

# Using a Table

matrix.py includes a built-in `Table` component for displaying labeled fields:

```python
from matrix import Bot, Table

bot = Bot()


@bot.command()
async def user_info(ctx):
    table = Table(title="User Info")

    table.add_field("Name", "Astra")
    table.add_field("Role", "Engineer")

    await ctx.reply(component=table)
```

Each field is added with `add_field`:

```python
table.add_field("Name", "Astra")
```

The first argument is the field name, and the second is its value.

# Setting the Column Count

Tables use two columns by default. You can change this with `column_count`:

```python
table = Table(
    title="Server Info",
    column_count=3,
)

table.add_field("Name", "Example")
table.add_field("Status", "Online")
table.add_field("Users", "42")
```

Fields are placed into rows using the configured number of columns. An incomplete
final row is automatically padded with empty cells. Fields are kept in the order in
which they are added.

The column count must be greater than zero:

```python
Table(title="Invalid", column_count=0)
# Raises ValueError
```

# Plain-Text Rendering

Use `to_plain_text` to render a component without HTML:

```python
table = Table(title="User Info")
table.add_field("Name", "Astra")
table.add_field("Role", "Engineer")

text = table.to_plain_text()
```

The result is:

```text
User Info
Name: Astra
Role: Engineer
```

# HTML Rendering

Use `render` to generate the HTML representation:

```python
html = table.render()
```

Calling `str` on a table produces the same result:

```python
html = str(table)
```

Table titles, field names, and field values are automatically HTML-escaped.

For example, a field added with a value of `"<online>"` is rendered as
`&lt;online&gt;`, so user-provided values cannot be interpreted as HTML markup.

# Creating a Custom Component

To create another kind of component, subclass `Component` and implement both
rendering methods:

```python
from html import escape

from matrix.component import Component


class Status(Component):
    def __init__(self, name: str, online: bool):
        self.name = name
        self.online = online

    def to_plain_text(self) -> str:
        state = "online" if self.online else "offline"
        return f"{self.name}: {state}"

    def render(self) -> str:
        state = "online" if self.online else "offline"
        return f"<strong>{escape(self.name)}</strong>: {escape(state)}"
```

Custom components can be sent in exactly the same way as a `Table`:

```python
await ctx.reply(component=Status("Astra", online=True))
```
