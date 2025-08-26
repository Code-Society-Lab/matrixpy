from typing import Callable


def cooldown(rate: int, period: float) -> Callable:
    """
    Decorator to cooldown a command.

    :param rate: The number of request a user can send.
    :type rate: int
    :param period: The period in seconds of the cooldown.
    :type period: float
    """
    def wrapper(cmd):
        cmd.set_cooldown(rate, period)
        return cmd
    return wrapper
