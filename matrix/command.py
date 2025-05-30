import asyncio
from typing import Any, Callable, Coroutine


Callback = Callable[..., Coroutine[Any, Any, Any]]
Context = 'Context'


class Command:
    def __init__(self, func: Callback, **kwargs: Any):
        name = kwargs.get("name") or func.__name__

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Commands must be coroutines")

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")

        self.name = name
        self._callback = func

    @property
    def callback(self) -> Callback:
        return self._callback

    # I believie that for now we don't have any use to return data
    def __call__(self, ctx: Context, *args, **kwargs) -> None:
        await self.callback(ctx, *args, **kwargs)

    # add checks (and logic for itk)

    # add cooldown (and logic for it)

    # _parse argument

