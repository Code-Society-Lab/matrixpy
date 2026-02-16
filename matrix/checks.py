from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .command import Command


def cooldown(rate: int, period: float) -> Callable:
    """
    Decorator to cooldown a command.

    :param rate: The number of request a user can send.
    :type rate: int
    :param period: The period in seconds of the cooldown.
    :type period: float
    """

    def wrapper(cmd: "Command") -> "Command":
        cmd.set_cooldown(rate, period)
        return cmd

    return wrapper
