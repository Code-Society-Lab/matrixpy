import pytest
from matrix.bot import Bot
from matrix.message import Message
from matrix.errors import MatrixError
from unittest.mock import AsyncMock, MagicMock
from nio import RoomMessageText


@pytest.fixture
def message_default():
    bot = Bot(config="tests/config_fixture.yaml")

    bot.client = MagicMock()
    bot.client.room_send = AsyncMock()
    bot.log = MagicMock()
    bot.log.getChild.return_value = MagicMock()

    return Message(bot)


@pytest.fixture
def event():
    return RoomMessageText.from_dict(
        {
            "content": {"body": "hello", "msgtype": "m.text"},
            "event_id": "$id",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )


@pytest.mark.asyncio
async def test_send_message_success(message_default):
    room_id = "!room:id"
    message = "Hello, world!"

    await message_default.send(room_id, message)
    message_default.bot.client.room_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_message_failure(message_default):
    room_id = "!room:id"
    message = "Hello, world!"

    message_default.bot.client.room_send.side_effect = Exception(
        "Failed to send message"
    )
    with pytest.raises(MatrixError, match="Failed to send message"):
        await message_default.send(room_id, message)


def test_make_content_with_html(message_default):
    body = "# Hello, world!"
    content = message_default._make_content(body, True)

    assert content["msgtype"] == message_default.TEXT_MESSAGE_TYPE
    assert content["body"] == body
    assert content["format"] == message_default.MATRIX_CUSTOM_HTML
    assert "formatted_body" in content


def test_make_content_without_html(message_default):
    body = "Hello, world!"
    content = message_default._make_content(body, False)

    assert content["msgtype"] == message_default.TEXT_MESSAGE_TYPE
    assert content["body"] == body
    assert "format" not in content
    assert "formatted_body" not in content


@pytest.mark.asyncio
async def test_send_reaction_success(message_default, event):
    room_id = "!room:id"

    await message_default.send_reaction(room_id, event, "hi")
    message_default.bot.client.room_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_reaction_failure(message_default, event):
    room_id = "!room:id"

    message_default.bot.client.room_send.side_effect = Exception(
        "Failed to send message"
    )
    with pytest.raises(MatrixError, match="Failed to send message"):
        await message_default.send_reaction(room_id, event, "🙏")
