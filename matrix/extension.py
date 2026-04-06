import inspect
import logging
from typing import Callable, Optional

from matrix.protocols import BotLike
from matrix.registry import Registry
from matrix.room import Room

logger = logging.getLogger(__name__)


class Extension(Registry):
    def __init__(self, name: str, prefix: Optional[str] = None) -> None:
        super().__init__(name, prefix=prefix)

        self.bot: Optional[BotLike] = None
        self._on_load: Optional[Callable] = None
        self._on_unload: Optional[Callable] = None

    def get_room(self, room_id: str) -> Room:
        if self.bot is None:
            raise RuntimeError("Extension is not loaded")
        return self.bot.get_room(room_id)

    def load(self, bot: BotLike) -> None:
        self.bot = bot

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
        self.bot = None

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
