import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from matrix.errors import AlreadyRegisteredError
from matrix.command import Command
from nio import RoomMessageText, MatrixRoom

from matrix.bot import Bot


@pytest.fixture
def bot():
    return Bot(
        username="grace",
        password="grace1234"
    )


@pytest.mark.asyncio
async def test_on_event_ignores_old_event(bot):
    bot.start_at = 100000

    mock_event = MagicMock(spec=RoomMessageText)
    mock_event.sender = "someone"
    mock_event.server_timestamp = 99999000

    bot.client.user = "bot_user"

    with patch.object(
        bot,
        "_dispatch",
        new_callable=AsyncMock
    ) as mock_dispatch:
        await bot._on_event(MatrixRoom("!roomid", "alias"), mock_event)
        mock_dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_dispatches(bot):
    called = False

    @bot.event()
    async def on_message(ctx):
        nonlocal called
        called = True

    event = RoomMessageText.from_dict(
        {
            "content": {
                "body": "hello world", "format": "org.matrix.custom.html",
                "formatted_body": "hello <strong>world</strong>",
                "msgtype": "m.text"
            },
            "event_id": "$152037280074GZeOm:matrix.org",
            "origin_server_ts": 1520372800469,
            "sender": "@grace:matrix.org",
            "type": "m.room.message",
            "unsigned": {
                "age": 598971425
            }
        }
    )

    with patch("matrix.context.Context", autospec=True) as MockContext:
        mock_ctx = MagicMock()
        mock_ctx.event = event
        MockContext.return_value = mock_ctx

        await bot._on_event(MatrixRoom("!room:matrix.org", "alias"), event)

    assert called, "Expected the event handler to be called"


@pytest.mark.asyncio
async def test_event_decorator_registers_handler(bot):
    @bot.event
    async def on_message(ctx):
        pass

    assert RoomMessageText in bot._handlers
    assert on_message in bot._handlers[RoomMessageText]


def test_command_decorator_registers_command(bot):
    @bot.command()
    async def hello(ctx):
        pass

    assert "hello" in bot.commands
    assert isinstance(bot.commands["hello"], Command)


def test_duplicate_command_raises(bot):
    @bot.command("echo")
    async def cmd1(ctx):
        pass

    with pytest.raises(AlreadyRegisteredError):
        @bot.command("echo")
        async def cmd2(ctx):
            pass
