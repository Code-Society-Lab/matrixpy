import logging

from typing import TYPE_CHECKING, Optional
from matrix.registry import Registry

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from matrix.bot import Bot


class Extension(Registry):
    def __init__(self, prefix: Optional[str] = None) -> None:
        super().__init__(prefix=prefix)

    async def on_load(self, bot: "Bot") -> None:
        """Called after the extension is fully loaded into the bot."""
        pass

    async def on_unload(self, bot: "Bot") -> None:
        """Called before the extension is removed from the bot."""
        pass

    def __repr__(self) -> str:
        return (
            f"<Extension name={self.name!r} prefix={self.prefix!r} "
            f"commands={list(self._commands)}"
            f"events={[t.__name__ for t in self._event_handlers]}"
            f"errors={[t.__name__ for t in self._error_handlers]}"">"
        )