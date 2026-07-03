from typing import Awaitable, TypeVar

from nio import ErrorResponse, Response

from matrix.errors import MatrixError

T = TypeVar("T", bound=Response)


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
