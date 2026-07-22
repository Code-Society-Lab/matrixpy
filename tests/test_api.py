from unittest.mock import AsyncMock, patch

import pytest
from nio import RoomSendResponse, RoomSendError

from matrix.errors import ConfigError, MatrixApiError, MatrixError
from matrix.api import matrix_call, with_retry


@pytest.mark.asyncio
async def test_matrix_call_with_success__expect_response_returned():
    async def call():
        return RoomSendResponse(event_id="$event123", room_id="!room:example.com")

    response = await matrix_call(call(), error_message="Failed to send message")

    assert response.event_id == "$event123"


@pytest.mark.asyncio
async def test_matrix_call_with_transport_exception__expect_matrix_api_error():
    async def call():
        raise Exception("Network error")

    with pytest.raises(MatrixApiError, match="Failed to send message: Network error"):
        await matrix_call(call(), error_message="Failed to send message")


@pytest.mark.asyncio
async def test_matrix_call_with_error_response__expect_matrix_error():
    async def call():
        return RoomSendError("not allowed", "M_FORBIDDEN")

    with pytest.raises(MatrixError, match="Failed to send message: .*M_FORBIDDEN"):
        await matrix_call(call(), error_message="Failed to send message")


@pytest.mark.asyncio
async def test_matrix_call_with_rate_limited_error_response__expect_retry_after_ms_set():
    async def call():
        return RoomSendError(
            "too many requests", "M_LIMIT_EXCEEDED", retry_after_ms=5000
        )

    with pytest.raises(MatrixApiError) as exc_info:
        await matrix_call(call(), error_message="Failed to send message")

    assert exc_info.value.retry_after_ms == 5000


@pytest.mark.asyncio
async def test_matrix_call_with_error_response_without_retry_after__expect_retry_after_ms_none():
    async def call():
        return RoomSendError("not allowed", "M_FORBIDDEN")

    with pytest.raises(MatrixApiError) as exc_info:
        await matrix_call(call(), error_message="Failed to send message")

    assert exc_info.value.retry_after_ms is None


def test_matrix_call_requires_keyword_error_message__expect_type_error():
    with pytest.raises(TypeError):
        matrix_call(None, "Failed to send message")


def test_matrix_call_requires_positional_coro__expect_type_error():
    with pytest.raises(TypeError):
        matrix_call(coro=None, error_message="Failed to send message")


@pytest.mark.asyncio
async def test_with_retry_with_success_first_try__expect_response_returned():
    call = AsyncMock(return_value="ok")

    result = await with_retry(lambda: call())

    assert result == "ok"
    assert call.await_count == 1


@pytest.mark.asyncio
async def test_with_retry_with_transient_matrix_error_then_success__expect_response_returned_after_retry():
    call = AsyncMock(side_effect=[MatrixApiError("rate limited"), "ok"])

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        result = await with_retry(lambda: call())

    assert result == "ok"
    assert call.await_count == 2
    sleep.assert_awaited_once_with(1.0)


@pytest.mark.asyncio
async def test_with_retry_exhausts_retries__expect_matrix_api_error_raised():
    call = AsyncMock(side_effect=MatrixApiError("still failing"))

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(MatrixApiError, match="still failing"):
            await with_retry(lambda: call(), retries=2)

    assert call.await_count == 3


@pytest.mark.asyncio
async def test_with_retry_with_non_matrix_exception__expect_immediate_raise_no_retry():
    call = AsyncMock(side_effect=Exception("boom"))

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        with pytest.raises(Exception, match="boom"):
            await with_retry(lambda: call())

    assert call.await_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_with_retry_with_non_api_matrix_error__expect_immediate_raise_no_retry():
    call = AsyncMock(side_effect=ConfigError("token"))

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        with pytest.raises(ConfigError):
            await with_retry(lambda: call())

    assert call.await_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_with_retry_uses_exponential_backoff__expect_increasing_delays():
    call = AsyncMock(
        side_effect=[
            MatrixApiError("fail 1"),
            MatrixApiError("fail 2"),
            MatrixApiError("fail 3"),
            "ok",
        ]
    )

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        result = await with_retry(lambda: call(), retries=3, base_delay=1.0)

    assert result == "ok"
    assert [call_args.args[0] for call_args in sleep.await_args_list] == [
        1.0,
        2.0,
        4.0,
    ]


@pytest.mark.asyncio
async def test_with_retry_with_retry_after_ms__expect_server_delay_honored():
    call = AsyncMock(
        side_effect=[MatrixApiError("rate limited", retry_after_ms=2500), "ok"]
    )

    with patch("matrix.api.asyncio.sleep", new_callable=AsyncMock) as sleep:
        result = await with_retry(lambda: call())

    assert result == "ok"
    sleep.assert_awaited_once_with(2.5)


def test_with_retry_requires_positional_func__expect_type_error():
    with pytest.raises(TypeError):
        with_retry(func=lambda: None)
