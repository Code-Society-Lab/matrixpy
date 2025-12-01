from typing import TYPE_CHECKING, Any, Coroutine, Callable
import inspect

if TYPE_CHECKING:
    from .command import Command  # pragma: no cover
    from .error import Error  # pragam: no cover
    from .group import Group  # pragma: no cover

    Callback = Callable[..., Coroutine[Any, Any, Any]]


class MatrixError(Exception):
    pass


class CommandError(MatrixError):
    pass


class CommandNotFoundError(CommandError):
    def __init__(self, cmd: str):
        super().__init__(f"Command with name '{cmd}' not found")


class AlreadyRegisteredError(CommandError):
    def __init__(self, cmd: Command):
        super().__init__(f"Command '{cmd}' is already registered")


class MissingArgumentError(CommandError):
    def __init__(self, param: inspect.Parameter):
        super().__init__(f"Missing required argument: '{param.name}'")


class CheckError(CommandError):
    def __init__(self, cmd: Command, check: Callback):
        super().__init__(f"'{check.__name__}' has failed for '{cmd.name}'")


class GroupError(CommandError):
    pass


class GroupAlreadyRegisteredError(GroupError):
    def __init__(self, group: Group):
        super().__init__(f"Group '{group}' is already registered")


class ConfigError(MatrixError):
    def __init__(self, error: str):
        super().__init__(f"Missing required configuration: '{error}'")


class CooldownError(CheckError):
    def __init__(self, cmd: Command, check: Callback, retry: float):
        self.retry = retry
        super().__init__(cmd, check)
