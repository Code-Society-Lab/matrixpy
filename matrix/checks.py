from .errors import CooldownError
from collections import defaultdict
from collections.abc import Callable
from typing import DefaultDict, TypeVar, Awaitable, Any
from functools import wraps
from time import monotonic


T = TypeVar("T", bound=Callable[..., Awaitable[Any]])


class Cooldown:
    """
    Class to cooldown a command.

    Calls are rate-limited per unique ctx.sender, assumed to be a user ID string.

    :param rate: The number of allowed invocations per user.
    :type rate: float
    :param period: The cooldown window in seconds.
    :type period: float

    :raise CooldownError: If a cooldown error occure.
    """

    def __init__(self, rate: float, period: float) -> None:
        self.rate: int = int(rate)
        self.period: float = float(period)
        self.calls: DefaultDict[str, list[float]] = defaultdict(list)

    def __call__(self, func: T) -> T:
        @wraps(func)
        async def wrapper(*args: Any) -> Any:
            ctx = args[0] if args else None
            if ctx is None or not hasattr(ctx, "sender"):
                raise CooldownError("context or sender info.")

            now = monotonic()
            user_id = ctx.sender

            calls = [t for t in self.calls[user_id] if now - t < self.period]
            self.calls[user_id] = calls

            if len(calls) >= self.rate:
                oldest = min(calls)
                retry = self.period - (now - oldest)
                await ctx.reply(
                    f"You're on cooldown. Try again in {retry:.1f} seconds."
                )
                return

            result = await func(*args)
            self.calls[user_id].append(now)
            return result

        return wrapper


def cooldown(rate: float, period: float) -> Cooldown:
    """
    Decorator to cooldown a command.

    :param rate: The number of request a user can send.
    :type rate: float
    :param period: The period in seconds of the cooldown.
    :type period: float
    """

    return Cooldown(rate, period)
