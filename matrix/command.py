import asyncio
import inspect
from matrix.errors import MissingArgumentError
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Callable,
    Coroutine,
    get_type_hints
)


if TYPE_CHECKING:
    from matrix.context import Context


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

        self._help: str = kwargs.get("help", "")
        self._usage: str = kwargs.get("usage", "")
        self.description: str = kwargs.get("description", "")

        self._on_error: Optional[ErrorCallback] = None

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

    @property
    def usage(self) -> str:
        """
        Returns the usage string for the command. Builds one if none has been
        set at the command initalization.

        :return: A usage string.
        :rtype: str
        """
        if self._usage:
            return self._usage

        params = " ".join(f"<{p.name}>" for p in self.params)
        return f"{self.name} {params}"

    @property
    def help(self) -> str:
        """
        Returns the help text for the command.

        :return: The help text, cleaned of leading whitespace.
        :rtype: str
        """
        return inspect.cleandoc(self._help)

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

    def error(self) -> Callable:
        """
        Decorator to register a custom error handler for the command.

        :return: A decorator that registers the error handler.
        :rtype: Callable
        :raises TypeError: If the decorated function is not a coroutine.
        """

        def wrapper(func: ErrorCallback) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The error handler must be a coroutine.')

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
        if self._on_error:
            await self._on_error(ctx, error)
            return
        ctx.logger.exception("error while executing command '%s'", self)

    async def __call__(self, ctx: "Context") -> None:
        """
        Execute the command with parsed arguments.

        :param ctx: The command execution context.
        :type ctx: Context
        """
        parsed_args = self._parse_arguments(ctx)
        await self.callback(ctx, *parsed_args)

    def __eq__(self, other) -> bool:
        return self.name == other

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
