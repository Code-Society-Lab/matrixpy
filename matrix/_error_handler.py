import inspect
from typing import Callable, Dict, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., object])


def resolve_error_handler(
    handlers: Dict[type[Exception], F], error: Exception
) -> Optional[F]:
    """Look up the handler registered for the error's type or nearest base class."""
    for cls in inspect.getmro(type(error)):
        if cls in handlers:
            return handlers[cls]
    return None
