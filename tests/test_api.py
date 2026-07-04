import pytest
from nio import RoomSendResponse, RoomSendError

from matrix.errors import MatrixError
from matrix.api import matrix_call


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
