import pytest
from unittest.mock import MagicMock, AsyncMock
from nio import MatrixRoom, RoomMessageText
from matrix.errors import MatrixError
from matrix.bot import Bot
from matrix.context import Context


@pytest.fixture
def bot():
    bot = Bot(username="grace", password="grace1234")

    bot.client = MagicMock()
    bot.client.room_send = AsyncMock()
    bot.log = MagicMock()
    bot.log.getChild.return_value = MagicMock()

    return bot


@pytest.fixture
def room():
    room = MatrixRoom(room_id="!room:id", own_user_id="grace")
    room.name = "Test Room"
    return room


@pytest.fixture
def event():
    return RoomMessageText.from_dict({
        "content": {"body": "!echo hello world", "msgtype": "m.text"},
        "event_id": "$id",
        "origin_server_ts": 123456,
        "sender": "@user:matrix.org",
        "type": "m.room.message",
    })


def test_context_initialization(bot, room, event):
    ctx = Context(bot, room, event)

    assert ctx.bot == bot
    assert ctx.room == room
    assert ctx.event == event
    assert ctx.body == "!echo hello world"
    assert ctx.sender == "@user:matrix.org"
    assert ctx.room_id == "!room:id"
    assert ctx.room_name == "Test Room"
    assert ctx.prefix == "!"
    assert ctx.command is None
    assert ctx._args == ["!echo", "hello", "world"]


def test_args_without_command(bot, room, event):
    ctx = Context(bot, room, event)
    assert ctx.args == ["!echo", "hello", "world"]


def test_args_with_command(bot, room, event):
    ctx = Context(bot, room, event)
    ctx.command = MagicMock()
    assert ctx.args == ["hello", "world"]


def test_logger_property(bot, room, event):
    ctx = Context(bot, room, event)
    logger = ctx.logger
    assert logger is not None


@pytest.mark.asyncio
async def test_send_success(bot, room, event):
    ctx = Context(bot, room, event)
    await ctx.reply("Hello!")

    bot.client.room_send.assert_awaited_once_with(
        room_id="!room:id",
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": "Hello!",
            "format": "org.matrix.custom.html",
            "formatted_body": "<p>Hello!</p>",
        },
    )


@pytest.mark.asyncio
async def test_send_failure_raises_matrix_error(bot, room, event):
    bot.client.room_send.side_effect = Exception("API failure")
    ctx = Context(bot, room, event)

    with pytest.raises(MatrixError, match="Failed to send message: API failure"):
        await ctx.reply("Test failure")
