import pytest
from unittest.mock import AsyncMock, Mock
from nio import MatrixRoom, AsyncClient
from matrix.errors import MatrixError
from matrix.message import Message
from matrix.room import Room


@pytest.fixture
def matrix_room():
    room = Mock(spec=MatrixRoom)
    room.room_id = "!room:example.com"
    room.name = "Test Room"
    room.display_name = "Test Room"
    room.topic = "A test room"
    room.member_count = 5
    room.encrypted = False
    return room


@pytest.fixture
def client():
    client = AsyncMock(spec=AsyncClient)
    return client


@pytest.fixture
def room(matrix_room, client):
    return Room(matrix_room, client)


@pytest.fixture
def message(room, client):
    return Message(room=room, event_id="$event123", body="Hello world!", client=client)


@pytest.mark.asyncio
async def test_reply__expect_threaded_reply_message(message, client):
    mock_response = Mock()
    mock_response.event_id = "$reply456"
    client.room_send = AsyncMock(return_value=mock_response)

    result = await message.reply("Replying to you!")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["body"] == "Replying to you!"
    assert "m.relates_to" in content
    assert content["m.relates_to"]["m.in_reply_to"]["event_id"] == "$event123"
    assert isinstance(result, Message)
    assert result.id == "$reply456"


@pytest.mark.asyncio
async def test_reply_with_error__expect_matrix_error(message, client):
    client.room_send = AsyncMock(side_effect=Exception("Network error"))

    with pytest.raises(MatrixError, match="Failed to send reply"):
        await message.reply("This will fail")


@pytest.mark.asyncio
async def test_react__expect_reaction_sent(message, client):
    client.room_send = AsyncMock()

    await message.react("👍")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    assert call_args.kwargs["message_type"] == "m.reaction"
    content = call_args.kwargs["content"]
    assert content["m.relates_to"]["rel_type"] == "m.annotation"
    assert content["m.relates_to"]["event_id"] == "$event123"
    assert content["m.relates_to"]["key"] == "👍"


@pytest.mark.asyncio
async def test_react_with_error__expect_matrix_error(message, client):
    client.room_send = AsyncMock(side_effect=Exception("Failed to react"))

    with pytest.raises(MatrixError, match="Failed to add reaction"):
        await message.react("😀")


@pytest.mark.asyncio
async def test_edit__expect_message_updated(message, client):
    client.room_send = AsyncMock()

    await message.edit("Updated content")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["body"] == "* Updated content"
    assert content["m.new_content"]["body"] == "Updated content"
    assert content["m.relates_to"]["rel_type"] == "m.replace"
    assert content["m.relates_to"]["event_id"] == "$event123"
    assert message.body == "Updated content"


@pytest.mark.asyncio
async def test_edit_with_error__expect_matrix_error(message, client):
    client.room_send = AsyncMock(side_effect=Exception("Failed to edit"))

    with pytest.raises(MatrixError, match="Failed to edit message"):
        await message.edit("New content")


@pytest.mark.asyncio
async def test_delete__expect_message_redacted(message, client):
    client.room_redact = AsyncMock()

    await message.delete()

    client.room_redact.assert_awaited_once_with(
        room_id="!room:example.com", event_id="$event123"
    )


@pytest.mark.asyncio
async def test_delete_with_error__expect_matrix_error(message, client):
    client.room_redact = AsyncMock(side_effect=Exception("Failed to redact"))

    with pytest.raises(MatrixError, match="Failed to delete message"):
        await message.delete()


def test_message_properties__expect_correct_values(message, room, client):
    assert message.id == "$event123"
    assert message.event_id == "$event123"
    assert message.body == "Hello world!"
    assert message.room is room
    assert message.client is client


def test_message_repr__expect_formatted_string(message):
    result = repr(message)
    assert result == "<Message id='$event123' body='Hello world!'>"
