import pytest
from matrix.bot import Bot
from matrix.message import Message
from matrix.errors import MatrixError
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def message_default():
    bot = Bot(username="grace", password="grace1234")

    bot.client = MagicMock()
    bot.client.room_send = AsyncMock()
    bot.log = MagicMock()
    bot.log.getChild.return_value = MagicMock()

    return Message(bot)


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
