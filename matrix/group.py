import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, Callable, Coroutine

from .command import Command
from .errors import AlreadyRegisteredError, CommandNotFoundError

if TYPE_CHECKING:
    from .context import Context  # pragma: no cover

logger = logging.getLogger(__name__)

Callback = Callable[..., Coroutine[Any, Any, Any]]
ErrorCallback = Callable[["Context", Exception], Coroutine[Any, Any, Any]]


class Group(Command):
    def __init__(
        self,
        callback: Callback,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prefix: Optional[str] = None,
        parent: Optional[str] = None,
        usage: Optional[str] = None,
        cooldown: Optional[tuple[int, float]] = None,
    ):
        self.commands: Dict[str, Command] = {}

        super().__init__(
            callback,
            name=name,
            description=description,
            prefix=prefix,
            parent=parent,
            usage=usage,
            cooldown=cooldown,
        )

    def _build_usage(self) -> str:
        return f"{self.prefix}{self.name} [subcommand]"

    def get_command(self, cmd_name: str) -> Command:
        if cmd := self.commands.get(cmd_name):
            return cmd
        raise CommandNotFoundError(cmd_name)

    def command(self, name: Optional[str] = None) -> Callable[[Callback], Command]:
        """
        Decorator to register a coroutine function as a command handler.

        The command name defaults to the function name unless
        explicitly provided.

        :param name: The name of the command. If omitted, the function
                     name is used.
        :type name: str, optional
        :raises TypeError: If the decorated function is not a coroutine.
        :raises ValueError: If a command with the same name is registered.
        :return: Decorator that registers the command handler.
        :rtype: Callback
        """

        def wrapper(func: Callback) -> Command:
            cmd = Command(func, name=name, prefix=self.prefix, parent=self.name)
            return self.register_command(cmd)

        return wrapper

    def register_command(self, cmd: Command) -> Command:
        if cmd in self.commands:
            raise AlreadyRegisteredError(cmd)

        self.commands[cmd.name] = cmd
        logger.debug("command '%s' registered for group '%s'", cmd, self)

        return cmd

    async def invoke(self, ctx: "Context") -> None:
        if ctx.args and (subcommand := ctx.args.pop(0)):
            ctx.subcommand = self.get_command(subcommand)
            await ctx.subcommand(ctx)
        else:
            await self.callback(ctx)


def group(
    name: str,
    *,
    description: Optional[str] = None,
    prefix: Optional[str] = None,
    parent: Optional[str] = None,
    usage: Optional[str] = None,
    cooldown: Optional[tuple[int, float]] = None,
) -> Callable[[Callback], Group]:
    """
    Decorator to create a group with a callback.

    This is equivalent to @bot.group() but for creating groups
    without immediately registering them to a bot.

    ## Example

    ```python
    @group("math", description="Math operations")
    async def math(ctx):
        await ctx.reply("Math help")


    @math.command()
    async def add(ctx, a: int, b: int):
        await ctx.reply(f"{a + b}")


    bot.register_group(math)
    ```
    """

    def decorator(func: Callback) -> Group:
        return Group(
            func,
            name=name,
            description=description,
            prefix=prefix,
            parent=parent,
            usage=usage,
            cooldown=cooldown,
        )

    return decorator
