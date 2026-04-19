from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .command import Command


def cooldown(rate: int, period: float) -> Callable:
    """
    Decorator to cooldown a command.

    ## Example

    ```python
    @cooldown(rate=3, period=10)
    @bot.command("hello")
    async def hello(ctx: Context) -> None:
        await ctx.reply("Hello!")

    @hello.error(CooldownError)
    async def hello_error(ctx: Context, error: CooldownError) -> None:
        await ctx.reply(f"Slow down! Try again in {error.retry:.1f}s.")
    ```
    """

    def wrapper(cmd: "Command") -> "Command":
        cmd.set_cooldown(rate, period)
        return cmd

    return wrapper
