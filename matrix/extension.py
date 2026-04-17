import inspect
import logging
from typing import Callable

from matrix.protocols import BotLike
from matrix.registry import Registry
from matrix.config import Config
from matrix.room import Room

logger = logging.getLogger(__name__)


class Extension(Registry):
    def __init__(self, name: str, prefix: str | None = None) -> None:
        super().__init__(name, prefix=prefix)

        self._bot: BotLike | None = None
        self._on_load: Callable | None = None
        self._on_unload: Callable | None = None

    @property
    def bot(self) -> BotLike:
        assert self._bot, "Extension is not loaded"
        return self._bot

    @property
    def config(self) -> Config:
        return self.bot.config

    def get_room(self, room_id: str) -> Room | None:
        """Retrieve a `Room` instance by its Matrix room ID.

        Returns the `Room` object corresponding to `room_id` if it exists in
        the client's known rooms. Returns `None` if the room cannot be found.

        ## Example

        ```python
        room = extension.get_room("!abc123:matrix.org")
        if room:
            print(room.name)
        ```
        """
        return self.bot.get_room(room_id)

    def load(self, bot: BotLike) -> None:
        self._bot = bot

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
        self._bot = None

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
