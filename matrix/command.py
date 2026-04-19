import inspect
import types

from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    Optional,
    Callable,
    Coroutine,
    List,
    get_type_hints,
    DefaultDict,
    get_args,
    get_origin,
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
    """

    def __init__(
        self,
        func: Callback,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prefix: Optional[str] = None,
        parent: Optional[str] = None,
        usage: Optional[str] = None,
        cooldown: Optional[tuple[int, float]] = None,
    ):
        if name is not None and not isinstance(name, str):
            raise TypeError("Name must be a string.")

        self.name: str = name or func.__name__
        self.callback = func
        self.checks: List[Callback] = []

        self.description: str = description or ""
        self.prefix: str = prefix or ""
        self.parent: str = parent or ""
        self.usage: str = usage or self._build_usage()
        self.help: str = self._build_help()

        self._before_invoke_callback: Optional[Callback] = None
        self._after_invoke_callback: Optional[Callback] = None
        self._on_error: Optional[ErrorCallback] = None
        self._error_handlers: dict[type[Exception], ErrorCallback] = {}

        self.cooldown_rate: Optional[int] = None
        self.cooldown_period: Optional[float] = None
        self.cooldown_calls: DefaultDict[str, deque[float]] = defaultdict(deque)

        if cooldown:
            self.set_cooldown(*cooldown)

    @property
    def callback(self) -> Callback:
        """
        Returns the coroutine function for this command.
        """
        return self._callback

    @callback.setter
    def callback(self, func: Callback) -> None:
        """
        Sets the coroutine function for the command and extracts type
        hints and parameters.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Commands must be coroutines")

        self._callback = func

        self.type_hints = get_type_hints(func)
        self.signature = inspect.signature(func)
        self.params = list(self.signature.parameters.values())[1:]

    def _build_help(self) -> str:
        """
        Returns the help text for the command.
        """
        default_help = f"{self.description}\n\nusage: {self.usage}"
        return inspect.cleandoc(default_help)

    def _build_usage(self) -> str:
        """
        Builds and returns the default usage string for the command.
        set at the command initalization.
        """
        params = " ".join(f"[{p.name}]" for p in self.params)
        command_name = self.name

        if self.parent:
            command_name = f"{self.parent} {self.name}"

        return f"{self.prefix}{command_name} {params}"

    def _parse_arguments(self, ctx: "Context") -> list[Any]:
        args = ctx.args
        parsed_args = []

        for i, param in enumerate(self.params):
            param_type = self.type_hints.get(param.name, str)

            if i >= len(args):
                if param.default is not inspect.Parameter.empty:
                    parsed_args.append(param.default)
                    continue
                raise MissingArgumentError(param)

            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                parsed_args.extend(
                    self._convert_type(param_type, arg) for arg in args[i:]
                )
                return parsed_args

            converted_arg = self._convert_type(param_type, args[i])
            parsed_args.append(converted_arg)

        return parsed_args

    def _convert_type(self, param_type: type, value: str) -> Any:
        origin = get_origin(param_type)

        if origin is Union or isinstance(param_type, types.UnionType):
            union_types = get_args(param_type)

            for union_type in union_types:
                if union_type is type(None):
                    continue

                try:
                    return union_type(value)
                except (ValueError, TypeError):
                    continue

            return value

        try:
            return param_type(value)
        except (ValueError, TypeError):
            return value

    def check(self, func: Callback) -> None:
        """
        Register a check callback

        ## Example

        ```python
        @bot.command("secret")
        async def secret(ctx: Context) -> None:
            await ctx.reply("Access granted!")

        @secret.check
        async def is_allowed(ctx: Context) -> bool:
            return ctx.sender == "@admin:matrix.org"
        ```
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Checks must be coroutine")

        self.checks.append(func)

    def set_cooldown(self, rate: int, period: float) -> None:
        self.cooldown_rate = rate
        self.cooldown_period = period

        async def cooldown_function(ctx: "Context") -> bool:
            if ctx is None or not hasattr(ctx, "sender"):
                return False

            if self.cooldown_period is None or self.cooldown_rate is None:
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

        ## Example

        ```python
        @bot.command("ping")
        async def ping(ctx: Context) -> None:
            await ctx.reply("Pong!")

        @ping.before_invoke
        async def before_ping(ctx: Context) -> None:
            print(f"ping invoked by {ctx.sender}")
        ```
        """

        if not inspect.iscoroutinefunction(func):
            raise TypeError("The hook must be a coroutine.")

        self._before_invoke_callback = func

    def after_invoke(self, func: Callback) -> None:
        """
        Registers a coroutine to be called after the command is invoked.

        ## Example

        ```python
        @bot.command("ping")
        async def ping(ctx: Context) -> None:
            await ctx.reply("Pong!")

        @ping.after_invoke
        async def after_ping(ctx: Context) -> None:
            print(f"ping completed for {ctx.sender}")
        ```
        """

        if not inspect.iscoroutinefunction(func):
            raise TypeError("The hook must be a coroutine.")

        self._after_invoke_callback = func

    def error(self, exception: Optional[type[Exception]] = None) -> Callable:
        """
        Decorator used to register an error handler for this command.

        ## Example

        ```python
        @bot.command("div")
        async def div(ctx: Context, a: int, b: int) -> None:
            await ctx.reply(f"{a / b}")

        @div.error(ZeroDivisionError)
        async def div_error(ctx: Context, error: ZeroDivisionError) -> None:
            await ctx.reply("Cannot divide by zero!")

        @div.error(MissingArgumentError)
        async def div_missing(ctx: Context, error: MissingArgumentError) -> None:
            await ctx.reply(f"Missing argument: {error}")
        ```
        """

        def wrapper(func: ErrorCallback) -> Callable:
            if not inspect.iscoroutinefunction(func):
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

    async def invoke(self, ctx: "Context") -> None:
        parsed_args = self._parse_arguments(ctx)
        await self.callback(ctx, *parsed_args)

    async def _invoke(self, ctx: "Context") -> None:
        try:
            for check in self.checks:
                if not await check(ctx):
                    raise CheckError(self, check)

            if self._before_invoke_callback:
                await self._before_invoke_callback(ctx)

            await self.invoke(ctx)

            if self._after_invoke_callback:
                await self._after_invoke_callback(ctx)
        except Exception as error:
            await self.on_error(ctx, error)

    async def __call__(self, ctx: "Context") -> None:
        """
        Execute the command with parsed arguments.
        """
        await self._invoke(ctx)

    def __eq__(self, other: object) -> bool:
        return self.name == other

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
