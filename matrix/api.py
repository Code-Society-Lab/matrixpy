import asyncio
from typing import Awaitable, Iterable, TypeVar

from nio import ErrorResponse, Response

from matrix.errors import MatrixError

T = TypeVar("T", bound=Response)
R = TypeVar("R")


async def matrix_call(coro: Awaitable[T], /, *, error_message: str) -> T:
    """Await `coro`, translating any failure into a `MatrixError`.

    matrix-nio's `AsyncClient` methods don't raise on API-level errors; they
    return an `ErrorResponse` instead of raising. This wraps a single call so
    both transport-level exceptions and nio `ErrorResponse` results become a
    `MatrixError` carrying `error_message`.

    ## Example

    ```python
    response = await matrix_call(
        self.client.room_kick(room_id=self.room_id, user_id=user_id),
        error_message="Failed to kick user",
    )
    ```
    """
    try:
        response = await coro
    except Exception as e:
        raise MatrixError(f"{error_message}: {e}") from e

    if isinstance(response, ErrorResponse):
        raise MatrixError(f"{error_message}: {response}")

    return response


async def bounded_gather(
    coros: Iterable[Awaitable[R]],
    /,
    *,
    max_concurrent: int = 8,
) -> list[R]:
    """Run `coros` concurrently, limited to `max_concurrent` at a time.

    Behaves like `asyncio.gather`, but never runs more than `max_concurrent`
    awaitables at once. Useful for fanning out many API calls (e.g.
    broadcasting to many rooms) without overwhelming a shared rate limit by
    firing every request at once. The first exception raised by any
    coroutine cancels the rest and propagates immediately, same as
    `asyncio.gather`'s default behavior.

    ## Example

    ```python
    messages = await bounded_gather(
        (room.send(content) for room in rooms), max_concurrent=8
    )
    ```
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run(coro: Awaitable[R]) -> R:
        async with semaphore:
            return await coro

    return await asyncio.gather(*[_run(coro) for coro in coros])
