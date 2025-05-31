import asyncio
import inspect
from typing import Any, Callable, Coroutine, get_type_hints
from matrix.context import Context
from matrix.errors import CommandError, MissingArgumentError


Callback = Callable[..., Coroutine[Any, Any, Any]]
ErrorCallback = Callable[[Context, Exception], Coroutine]


class Command:
    def __init__(self, func: Callback, **kwargs: Any):
        name = kwargs.get("name") or func.__name__

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")

        self.name = name
        self.callback = func

        self._help = kwargs.get("help")
        self._usage = kwargs.get("usage", None)
        self.description = kwargs.get("description")

        self._on_error = None

    @property
    def callback(self) -> Callback:
        return self._callback

    @property
    def usage(self):
        if self._usage:
            return self._usage

        params = " ".join(f"<{p.name}>" for p in self.params)
        return f"{self.name} {params}"

    @property
    def help(self):
        return inspect.cleandoc(self._help)

    @callback.setter
    def callback(self, func: Callback) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Commands must be coroutines")

        self._callback = func

        self.type_hints = get_type_hints(func)
        self.signature = inspect.signature(func)
        self.params = list(self.signature.parameters.values())[1:]

    def _parse_arguments(self, ctx: Context) -> list[Any]:
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

    def error(self):
        """Decorator to register a custom error handler for the command."""

        def wrapper(func: ErrorCallback) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The error handler must be a coroutine.')

            self._on_error = func
            return func
        return wrapper

    async def on_error(self, ctx: Context, error: CommandError):
        if self._on_error:
            await self._on_error(ctx, error)
            return
        ctx.logger.exception("error while executing command '%s'", self)

    async def __call__(self, ctx: Context) -> None:
        """Execute the command with parsed arguments."""
        parsed_args = self._parse_arguments(ctx)
        await self.callback(ctx, *parsed_args)

    def __eq__(self, other):
        return isinstance(other, Command) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
