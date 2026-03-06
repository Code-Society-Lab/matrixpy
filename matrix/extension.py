import logging
import inspect

from typing import Any, Callable, Coroutine, Optional
from matrix.registry import Registry

logger = logging.getLogger(__name__)


class Extension(Registry):
    def __init__(self, name: str, prefix: Optional[str] = None) -> None:
        super().__init__(name, prefix=prefix)
        self._on_load: Optional[Callable] = None
        self._on_unload: Optional[Callable] = None

    def load(self) -> None:
        if self._on_load:
            self._on_load()

    def on_load(self, func: Callable) -> Callable:
        """Decorator to register a function to be called after this extension
        is loaded into the bot.

        ## Example

        ```python
        @extension.on_load
        def setup():
            print("extension loaded")
        ```
        """
        if inspect.iscoroutinefunction(func):
            raise TypeError("on_load handler must not be a coroutine")
        self._on_load = func
        return func

    def unload(self) -> None:
        if self._on_unload:
            self._on_unload()

    def on_unload(self, func: Callable) -> Callable:
        """Decorator to register a function to be called before this extension
        is unloaded from the bot.

        ## Example

        ```python
        @extension.on_unload
        def teardown():
            print("extension unloaded")
        ```
        """
        if inspect.iscoroutinefunction(func):
            raise TypeError("on_unload handler must not be a coroutine")
        self._on_unload = func
        return func
