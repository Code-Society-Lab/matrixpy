"""A simple, developer-friendly library to create powerful Matrix bots."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("matrix-python")
except PackageNotFoundError:
    from matrix._version import version as __version__

from .bot import Bot
from .group import Group, group
from .config import Config
from .context import Context
from .command import Command
from .help import HelpCommand
from .checks import cooldown
from .room import Room

__all__ = [
    "Bot",
    "Group",
    "group",
    "Config",
    "Command",
    "Context",
    "HelpCommand",
    "cooldown",
    "Room",
]
