# What is a Command?
A command is a special message that tells your bot to do something specific. Commands start with a prefix (like `!`) followed by the command name and optional arguments.

Let's break down this example command message:
```bash
!greet Alice
```

! - The prefix that identifies this as a command
greet - The command name that tells the bot what action to perform
Alice - An argument (parameter) passed to the command

When a user sends this message, your bot:
1. Recognizes the prefix !
2. Looks for a command named greet
3. Executes the command's function
4. Passes Alice as a parameter to that function

#### Command vs Regular Message
Your bot receives ALL messages in rooms it's in, but only processes messages that start with the prefix as commands. Regular messages are ignored (unless you specifically handle them with event handlers, which are covered [here](events.md)).

# Creating Your First Command
Let's create a simple command that responds with "Pong 🏓" when someone types `!ping`.

Commands are created using the `@bot.command()` decorator (see [`Bot`](../reference/bot.md)):
```python
from matrix import Bot

bot = Bot(config="config.yaml")

@bot.command()
async def ping(ctx):
    await ctx.reply("Pong 🏓")

bot.start()
```

### Adding a Description
Make your command clearer by adding a description:
```python
@bot.command(description="Checks if the bot is responding")
async def ping(ctx):
    await ctx.reply("Pong 🏓")
```
This description shows up in the help command when users type !help ping. 

### Customizing the Command Name
Sometimes you want the command name to be different from the function name:
```python
@bot.command(name="hello", description="Greets you!")
async def greeting_function(ctx):
    await ctx.reply("Hello! Welcome! 👋")
```
Now users type !hello, but your function is named greeting_function.

# Context
As you saw, every command must have a ctx (context) parameter. The [`Context`](../reference/context.md) object contains everything you need to know about how the command was called:

- Who called the command
- Where it was called (which room)
- What arguments were provided
- How to respond to the command

#### Accessing Context Information
```python
@bot.command()
async def whoami(ctx):
    # Who sent the command?
    sender = ctx.sender  # "@alice:example.com"
    
    # What room are we in?
    room_name = ctx.room_name  # "General Chat"
    room_id = ctx.room_id  # "!abc123:example.com"
    
    # What was the message?
    message = ctx.body  # "!whoami"
    
    # Send all this info back
    await ctx.reply(f"You are {sender} in {room_name} ({room_id}) and your message was {message}")
```

#### Common Context Attributes
| Attribute | Description | Example |
|-----------|-------------|---------|
| `ctx.sender` | User ID who sent the command | `"@alice:example.com"` |
| `ctx.room_id` | Unique room identifier | `"!abc123:example.com"` |
| `ctx.room_name` | Human-readable room name | `"General Chat"` |
| `ctx.body` | The full message text | `"!greet Alice"` |
| `ctx.args` | List of arguments after command | `["Alice"]` |
| `ctx.command` | The Command object itself | `Command(name="greet")` |
| `ctx.bot` | The bot instance | `Bot(...)` |
| `ctx.logger` | Logger for this room | `Logger(...)` |

#### Responding to Commands
The most common thing you'll do with context is send responses:
```python
@bot.command()
async def echo(ctx):
    await ctx.reply(f"You said: {ctx.body}")
```

# Parameters
Some commands might need additional information from the user. These are called parameters or arguments.

Add parameters to your command function after ctx:
```python
@bot.command(description="Greets a specific person")
async def greet(ctx, name: str):
    await ctx.reply(f"Hello, {name}!")
```
**Usage:** `!greet Alice` → Bot responds: `Hello, Alice!`

#### Type Hints are Important!
Type hints tell commands what type of data to expect and how to convert the text into that type.

```python
@bot.command()
async def example(ctx, text: str, number: int, decimal: float):
    await ctx.reply(f"Text: {text}, Number: {number}, Decimal: {decimal}")
```
**Usage:** !example hello 42 3.14

Matrix.py Automatically converts:
- "hello" stays as string → "hello"
- "42" converts to int → 42
- "3.14" converts to float → 3.14

### Optional Parameters
Sometimes you want a parameter to be optional:
```python
@bot.command(description="Greets someone, or everyone")
async def greet(ctx, name: str = "everyone"):
    await ctx.reply(f"Hello, {name}!")
```
**Usage:**
- `!greet Alice` → "Hello, Alice! 👋"
- `!greet` → "Hello, everyone! 👋"

### Variable Number of Arguments
What if you want to accept any number of arguments?
```python
@bot.command(description="Joins words together")
async def join(ctx, *words: str):
    # words will be a tuple of all arguments
    result = " ".join(words)
    await ctx.reply(result)
```
**Usage:** `!join Hello world from Matrix` → "Hello world from Matrix"

### What Happens With Missing Parameters?
If a required parameter is missing, Matrix.py raises a [`MissingArgumentError`](../reference/errors.md):
```python
@bot.command()
async def divide(ctx, a: int, b: int):
    result = a / b
    await ctx.reply(f"{a} / {b} = {result}")
```
**Usage:** `!divide 10` → Error! Missing parameter `b`
