from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .command import Command
    from .context import Context


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


def is_admin() -> Callable:
    """
    Decorator to restrict a command to room admins (power level >= 100).

    ## Example

    ```python
    @is_admin()
    @bot.command("ban")
    async def ban(ctx: Context, user_id: str) -> None:
        await ctx.room.ban_user(user_id)

    @ban.error(CheckError)
    async def ban_error(ctx: Context, error: CheckError) -> None:
        await ctx.reply("You must be an admin to use this command.")
    ```
    """

    async def _is_admin(ctx: "Context") -> bool:
        return ctx.room.power_levels.get_user_level(ctx.sender) >= 100  # type: ignore[no-any-return]

    def wrapper(cmd: "Command") -> "Command":
        cmd.check(_is_admin)
        return cmd

    return wrapper


def is_moderator() -> Callable:
    """
    Decorator to restrict a command to room moderators (power level >= 50).

    ## Example

    ```python
    @is_moderator()
    @bot.command("kick")
    async def kick(ctx: Context, user_id: str) -> None:
        await ctx.room.kick_user(user_id)

    @kick.error(CheckError)
    async def kick_error(ctx: Context, error: CheckError) -> None:
        await ctx.reply("You must be a moderator to use this command.")
    ```
    """

    async def _is_moderator(ctx: "Context") -> bool:
        return ctx.room.power_levels.get_user_level(ctx.sender) >= 50  # type: ignore[no-any-return]

    def wrapper(cmd: "Command") -> "Command":
        cmd.check(_is_moderator)
        return cmd

    return wrapper
