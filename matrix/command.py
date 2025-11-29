import asyncio
import inspect

from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Callable,
    Coroutine,
    List,
    get_type_hints,
    DefaultDict,
)

from .errors import MissingArgumentError, CheckError, CooldownError
from time import monotonic
from collections import defaultdict, deque

if TYPE_CHECKING:
    from .context import Context  # pragma: no cover


Callback = Callable[..., Coroutine[Any, Any, Any]]
ErrorCallback = Callable[["Context", Exception], Coroutine[Any, Any, Any]]


class Command:
    """
    Represents a command that can be executed with a context and arguments.

    :param func: The coroutine that is executed when the command is invoked.
    :type func: Callable[..., Coroutine[Any, Any, Any]]

    :keyword str name: Optional name. Defaults to the function's name.
    :keyword str help: Optional help text displayed to users.
    :keyword str usage: Optional usage string for the command.
    :keyword str description: Optional description of what the command does.

    :raises TypeError: If the provided name is not a string.
    :raises TypeError: If the provided callback is not a coroutine.
    """

    def __init__(self, func: Callback, **kwargs: Any):
        name: str = kwargs.get("name") or func.__name__

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")

        self.name: str = name
        self.callback = func
        self.checks: List[Callback] = []

        self.description: str = kwargs.get("description", "")
        self.prefix: str = kwargs.get("prefix", "")
        self.usage: str = kwargs.get("usage", self._build_usage())
        self.help: str = self._build_help()

        self._before_invoke: Optional[Callback] = None
        self._after_invoke: Optional[Callback] = None
        self._on_error: Optional[ErrorCallback] = None
        self._error_handlers: dict[type[Exception], ErrorCallback] = {}

        self.cooldown_rate: Optional[int] = None
        self.cooldown_period: Optional[float] = None
        self.cooldown_calls: DefaultDict[str, deque[float]] = defaultdict(deque)

        if cooldown := kwargs.get("cooldown"):
            self.set_cooldown(*cooldown)

    @property
    def callback(self) -> Callback:
        """
        Returns the coroutine function for this command.

        :return: The command's coroutine function.
        :rtype: Callback
        """
        return self._callback

    @callback.setter
    def callback(self, func: Callback) -> None:
        """
        Sets the coroutine function for the command and extracts type
        hints and parameters.

        :param func: The coroutine function to use.
        :type func: Callback
        :raises TypeError: If the provided function is not a coroutine.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Commands must be coroutines")

        self._callback = func

        self.type_hints = get_type_hints(func)
        self.signature = inspect.signature(func)
        self.params = list(self.signature.parameters.values())[1:]

    def _build_help(self) -> str:
        """
        Returns the help text for the command.

        :return: The help text for the command.
        :rtype: str
        """
        default_help = f"{self.description}\n\nusage: {self.usage}"
        return inspect.cleandoc(default_help)

    def _build_usage(self) -> str:
        """
        Builds and returns the default usage string for the command.
        set at the command initalization.

        :return: A usage string.
        :rtype: str
        """
        params = " ".join(f"[{p.name}]" for p in self.params)
        return f"{self.prefix}{self.name} {params}"

    def _parse_arguments(self, ctx: "Context") -> list[Any]:
        parsed_args = []

        for i, param in enumerate(self.params):
            param_type = self.type_hints.get(param.name, str)

            if i >= len(ctx.args):
                if param.default is not inspect.Parameter.empty:
                    parsed_args.append(param.default)
                else:
                    raise MissingArgumentError(param)
                continue

            converted_arg = param_type(ctx.args[i])
            parsed_args.append(converted_arg)

        return parsed_args

    def check(self, func: Callback) -> None:
        """
        Register a check callback

        :param func: The check callback
        :type func: Callback

        :raises TypeError: If the function is not a coroutine.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Checks must be coroutine")

        self.checks.append(func)

    def set_cooldown(self, rate: int, period: float) -> None:
        self.cooldown_rate = rate
        self.cooldown_period = period

        async def cooldown_function(ctx):
            if ctx is None or not hasattr(ctx, "sender"):
                return False

            now = monotonic()
            user_id = ctx.sender
            calls = self.cooldown_calls[user_id]

            while calls and now - calls[0] >= self.cooldown_period:
                calls.popleft()

            if len(calls) >= self.cooldown_rate:
                retry = self.cooldown_period - (now - calls[0])
                raise CooldownError(self, cooldown_function, retry)

            calls.append(now)
            return True

        self.checks.append(cooldown_function)

    def before_invoke(self, func: Callback) -> None:
        """
        Registers a coroutine to be called before the command is invoked.

        :param func: The coroutine function to call before command invocation.
        :type func: Callback

        :raises TypeError: If the function is not a coroutine.
        """

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("The hook must be a coroutine.")

        self._before_invoke = func

    def after_invoke(self, func: Callback) -> None:
        """
        Registers a coroutine to be called after the command is invoked.

        :param func: The coroutine function to call after command execution.
        :type func: Callback

        :raises TypeError: If the function is not a coroutine.
        """

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("The hook must be a coroutine.")

        self._after_invoke = func

    def error(self, exception: Optional[type[Exception]] = None) -> Callable:
        """
        Decorator used to register an error handler for this command.

        :param exception: Exception type to register the handler for.
        :type exception: Optional[Exception]
        :return: A decorator that registers the provided coroutine as an
            error handler and returns the original function.
        :rtype: Callable
        """

        def wrapper(func: ErrorCallback) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("The error handler must be a coroutine.")

            if exception:
                self._error_handlers[exception] = func
            else:
                self._on_error = func
            return func

        return wrapper

    async def on_error(self, ctx: "Context", error: Exception) -> None:
        """
        Executes the registered error handler if present.

        :param ctx: The command execution context.
        :type ctx: Context
        :param error: The exception that was raised.
        :type error: Exception
        """

        if handler := self._error_handlers.get(type(error)):
            await handler(ctx, error)
            return

        await ctx.bot.on_command_error(ctx, error)

        if self._on_error:
            await self._on_error(ctx, error)
        else:
            await ctx.send_help()

        ctx.logger.exception("error while executing command '%s'", self)
        raise error

    async def __before_invoke(self, ctx: "Context") -> None:
        for check in self.checks:
            if not await check(ctx):
                raise CheckError(self, check)

        if self._before_invoke:
            await self._before_invoke(ctx)

    async def __after_invoke(self, ctx: "Context") -> None:
        if self._after_invoke:
            await self._after_invoke(ctx)

    async def __call__(self, ctx: "Context") -> None:
        """
        Execute the command with parsed arguments.

        :param ctx: The command execution context.
        :type ctx: Context
        """
        try:
            await self.__before_invoke(ctx)

            parsed_args = self._parse_arguments(ctx)
            await self.callback(ctx, *parsed_args)

            await self.__after_invoke(ctx)
        except Exception as error:
            await self.on_error(ctx, error)

    def __eq__(self, other) -> bool:
        return self.name == other

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
