import asyncio
import inspect

import pytest
from nio import RoomSendResponse, RoomSendError

from matrix.errors import MatrixError
from matrix.api import bounded_gather, matrix_call


@pytest.mark.asyncio
async def test_matrix_call_with_success__expect_response_returned():
    async def call():
        return RoomSendResponse(event_id="$event123", room_id="!room:example.com")

    response = await matrix_call(call(), error_message="Failed to send message")

    assert response.event_id == "$event123"


@pytest.mark.asyncio
async def test_matrix_call_with_transport_exception__expect_matrix_error():
    async def call():
        raise Exception("Network error")

    with pytest.raises(MatrixError, match="Failed to send message: Network error"):
        await matrix_call(call(), error_message="Failed to send message")


@pytest.mark.asyncio
async def test_matrix_call_with_error_response__expect_matrix_error():
    async def call():
        return RoomSendError("not allowed", "M_FORBIDDEN")

    with pytest.raises(MatrixError, match="Failed to send message: .*M_FORBIDDEN"):
        await matrix_call(call(), error_message="Failed to send message")


def test_matrix_call_requires_keyword_error_message__expect_type_error():
    with pytest.raises(TypeError):
        matrix_call(None, "Failed to send message")


def test_matrix_call_requires_positional_coro__expect_type_error():
    with pytest.raises(TypeError):
        matrix_call(coro=None, error_message="Failed to send message")


@pytest.mark.asyncio
async def test_bounded_gather_with_success__expect_results_in_order():
    async def value(n):
        return n

    results = await bounded_gather([value(1), value(2), value(3)])

    assert results == [1, 2, 3]


@pytest.mark.asyncio
async def test_bounded_gather_limits_concurrency__expect_never_exceeds_max_concurrent():
    active = 0
    peak = 0

    async def task():
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return "done"

    results = await bounded_gather([task() for _ in range(10)], max_concurrent=3)

    assert results == ["done"] * 10
    assert peak == 3


@pytest.mark.asyncio
async def test_bounded_gather_with_exception__expect_it_propagates():
    async def ok():
        return "ok"

    async def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await bounded_gather([ok(), fail(), ok()])


def test_bounded_gather_default_max_concurrent__expect_eight():
    default = inspect.signature(bounded_gather).parameters["max_concurrent"].default

    assert default == 8


def test_bounded_gather_requires_positional_coros__expect_type_error():
    with pytest.raises(TypeError):
        bounded_gather(coros=[])
