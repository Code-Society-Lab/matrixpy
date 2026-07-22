import asyncio
from typing import Awaitable, Callable, TypeVar

from nio import ErrorResponse, Response

from matrix.errors import MatrixApiError

T = TypeVar("T", bound=Response)
R = TypeVar("R")


async def matrix_call(coro: Awaitable[T], /, *, error_message: str) -> T:
    """Await `coro`, translating any failure into a `MatrixApiError`.

    matrix-nio's `AsyncClient` methods don't raise on API-level errors; they
    return an `ErrorResponse` instead of raising. This wraps a single call so
    both transport-level exceptions and nio `ErrorResponse` results become a
    `MatrixApiError` carrying `error_message`. When the `ErrorResponse` is a
    rate limit with a `retry_after_ms`, that value is carried through
    unchanged on `MatrixApiError.retry_after_ms`.

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
        raise MatrixApiError(f"{error_message}: {e}") from e

    if isinstance(response, ErrorResponse):
        raise MatrixApiError(
            f"{error_message}: {response}", retry_after_ms=response.retry_after_ms
        )

    return response


async def with_retry(
    func: Callable[[], Awaitable[R]],
    /,
    *,
    retries: int = 3,
    base_delay: float = 1.0,
) -> R:
    """Call `func`, retrying on `MatrixApiError` with backoff.

    Retries up to `retries` times after the initial attempt (so up to
    `retries + 1` total calls). If the raised `MatrixApiError` carries a
    `retry_after_ms` (from the Matrix server), that wait is used exactly
    (converted to seconds); otherwise falls back to exponential delay
    (`base_delay * 2 ** attempt`). Only `MatrixApiError` triggers a retry;
    any other exception propagates.

    ## Example

    ```python
    message = await with_retry(lambda: room.send(content, notice=notice))
    ```
    """
    for attempt in range(retries + 1):
        try:
            return await func()
        except MatrixApiError as e:
            if attempt == retries:
                raise

            delay = base_delay * 2**attempt
            if e.retry_after_ms is not None:
                delay = e.retry_after_ms / 1000

            await asyncio.sleep(delay)

    raise AssertionError("unreachable")
