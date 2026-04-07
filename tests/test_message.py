import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from nio import MatrixRoom, AsyncClient, Event
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
    return AsyncMock(spec=AsyncClient)


@pytest.fixture
def room(matrix_room, client):
    return Room(matrix_room, client)


@pytest.fixture
def mock_event():
    event = MagicMock(spec=Event)
    event.event_id = "$event123"
    event.body = "Hello world!"
    event.sender = "@user:matrix.org"
    return event


@pytest.fixture
def message(room, client, mock_event):
    return Message(room=room, event=mock_event, client=client)


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


@pytest.mark.asyncio
async def test_fetch_reactions__expect_grouped_by_key(message, client):
    reaction_a = MagicMock()
    reaction_a.key = "👍"
    reaction_a.sender = "@alice:matrix.org"

    reaction_b = MagicMock()
    reaction_b.key = "👍"
    reaction_b.sender = "@bob:matrix.org"

    reaction_c = MagicMock()
    reaction_c.key = "👎"
    reaction_c.sender = "@carol:matrix.org"

    async def mock_relations(*args, **kwargs):
        for r in [reaction_a, reaction_b, reaction_c]:
            yield r

    client.room_get_event_relations = mock_relations

    result = await message.fetch_reactions()

    assert len(result) == 2
    thumbs_up = next(r for r in result if r.key == "👍")
    thumbs_down = next(r for r in result if r.key == "👎")
    assert sorted(thumbs_up.senders) == sorted(["@alice:matrix.org", "@bob:matrix.org"])
    assert thumbs_down.senders == ["@carol:matrix.org"]


@pytest.mark.asyncio
async def test_fetch_reactions_empty__expect_empty_list(message, client):
    async def mock_relations(*args, **kwargs):
        return
        yield  # make it an async generator

    client.room_get_event_relations = mock_relations

    result = await message.fetch_reactions()

    assert result == []


@pytest.mark.asyncio
async def test_fetch_reactions_with_error__expect_matrix_error(message, client):
    async def mock_relations(*args, **kwargs):
        raise Exception("Network error")
        yield

    client.room_get_event_relations = mock_relations

    with pytest.raises(MatrixError, match="Failed to fetch reactions"):
        await message.fetch_reactions()


def test_message_event_id__expect_correct_value(message):
    assert message.event_id == "$event123"


def test_message_body__expect_correct_value(message):
    assert message.body == "Hello world!"


def test_message_room__expect_correct_reference(message, room):
    assert message.room is room


def test_message_client__expect_correct_reference(message, client):
    assert message.client is client


def test_message_repr__expect_formatted_string(message):
    result = repr(message)
    assert result == "<Message id='$event123' body='Hello world!'>"
