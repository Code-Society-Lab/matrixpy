import pytest

from unittest.mock import AsyncMock, MagicMock, patch
from nio import MatrixRoom, RoomMessageText

from matrix.bot import Bot
from matrix.config import Config
from matrix.errors import (
    CheckError,
    CommandNotFoundError,
    AlreadyRegisteredError,
)


@pytest.fixture
def bot():
    bot = Bot("tests/config_fixture.yaml")

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
    return RoomMessageText.from_dict(
        {
            "content": {"body": "!echo hello world", "msgtype": "m.text"},
            "event_id": "$id",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )


def test_bot_init_with_config():
    bot = Bot(
        config=Config(
            username="grace",
            password="grace1234",
        )
    )

    assert bot.config.user_id == "grace"
    assert bot.config.password == "grace1234"
    assert bot.config.homeserver == "https://matrix.org"


def test_bot_init_with_invalid_config_file():
    with pytest.raises(FileNotFoundError):
        Bot("not-a-dict")


def test_auto_register_events_registers_known_events(bot):
    # Add a dummy coroutine named on_message_known to bot instance
    async def on_message_known(room, event):
        pass

    setattr(bot, "on_message_known", on_message_known)

    with patch.object(bot, "event", wraps=bot.event) as event:
        bot._auto_register_events()

    event.assert_any_call(on_message_known)


@pytest.mark.asyncio
async def test_dispatch_calls_all_handlers(bot):
    called = []

    async def handler1(room, event):
        called.append("h1")

    async def handler2(room, event):
        called.append("h2")

    bot._handlers[RoomMessageText].append(handler1)
    bot._handlers[RoomMessageText].append(handler2)

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "test", "msgtype": "m.text"},
            "event_id": "$id",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )
    room = MatrixRoom("!roomid:matrix.org", "room_alias")

    await bot._dispatch(room, event)
    assert "h1" in called
    assert "h2" in called


@pytest.mark.asyncio
async def test_on_event_ignores_self_events(bot):
    bot.start_at = None
    bot.client.user = "@grace:matrix.org"

    event = MagicMock(spec=RoomMessageText)
    event.sender = "@grace:matrix.org"
    event.server_timestamp = 123456789

    with patch.object(bot, "_dispatch", new_callable=AsyncMock) as dispatch:
        await bot._on_event(MatrixRoom("!room:matrix.org", "alias"), event)
        dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_ignores_old_events(bot, room, event):
    # Set start_at after event time
    bot.client.user = "@somebot:matrix.org"
    bot.start_at = event.server_timestamp / 1000 + 10

    bot._dispatch = AsyncMock()
    await bot._on_event(room, event)

    bot._dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_calls_error_handler(bot):
    bot._dispatch = AsyncMock(side_effect=Exception("boom"))

    custom_error_handler = AsyncMock()
    bot.error()(custom_error_handler)

    event = MagicMock(spec=RoomMessageText)
    event.sender = "@someone:matrix.org"
    event.server_timestamp = 999999999
    bot.start_at = 0
    bot.client.user = "@grace:matrix.org"

    await bot._on_event(MatrixRoom("!roomid", "alias"), event)
    custom_error_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_message_calls_process_commands(bot, room, event):
    with patch.object(bot, "_process_commands", new_callable=AsyncMock) as mock_proc:
        await bot.on_message(room, event)
        mock_proc.assert_awaited_once_with(room, event)


@pytest.mark.asyncio
async def test_on_ready(bot):
    await bot.on_ready()
    bot.log.info.assert_called_once_with("bot is ready")


@pytest.mark.asyncio
async def test_on_error_calls_custom_handler(bot):
    called = False

    @bot.error()
    async def custom_error_handler(e):
        nonlocal called
        called = True

    error = Exception("test error")
    await bot.on_error(error)

    assert called, "Custom error handler was not called"


@pytest.mark.asyncio
async def test_on_error_logs_when_no_handler(bot):
    bot._on_error = None
    error = Exception("test")

    await bot.on_error(error)
    bot.log.exception.assert_called_once_with("Unhandled error: '%s'", error)


@pytest.mark.asyncio
async def test_process_commands_executes_command(bot, event):
    called = False

    @bot.command()
    async def greet(ctx):
        nonlocal called
        called = True

    event.body = "!greet"
    room = MatrixRoom("!roomid:matrix.org", "alias")

    # Patch _build_context to return context with command assigned
    with patch.object(
        bot, "_build_context", new_callable=AsyncMock
    ) as mock_build_context:
        ctx = MagicMock()
        ctx.command = bot.commands["greet"]
        mock_build_context.return_value = ctx

        await bot._process_commands(room, event)

    assert called, "Expected command handler to be called"


@pytest.mark.asyncio
async def test_command_not_found_raises(bot):
    event = RoomMessageText.from_dict(
        {
            "content": {"body": "!nonexistent", "msgtype": "m.text"},
            "event_id": "$ev1",
            "origin_server_ts": 1234567890,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )

    room = MatrixRoom("!roomid", "alias")

    with patch("matrix.context.Context", autospec=True) as MockContext:
        mock_ctx = MagicMock()
        mock_ctx.body = "!nonexistent"
        MockContext.return_value = mock_ctx

        with pytest.raises(CommandNotFoundError):
            await bot._process_commands(room, event)


@pytest.mark.asyncio
async def test_bot_does_not_execute_when_global_check_fails(bot, event):
    called = False

    @bot.command()
    async def greet(ctx):
        nonlocal called
        called = True

    @bot.check
    async def global_check(ctx):
        return False

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "!greet", "msgtype": "m.text"},
            "event_id": "$ev2",
            "origin_server_ts": 1234567890,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )

    room = MatrixRoom("!roomid", "alias")

    with patch("matrix.context.Context", autospec=True) as MockContext:
        mock_ctx = MagicMock()
        mock_ctx.body = "!greet"
        mock_ctx.command = bot.commands["greet"]
        MockContext.return_value = mock_ctx

        with pytest.raises(CheckError):
            await bot._process_commands(room, event)

    assert not called, "Expected command handler not to be called"


@pytest.mark.asyncio
async def test_command_executes(bot):
    called = False

    @bot.command("ping")
    async def ping(ctx):
        nonlocal called
        called = True

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "!ping", "msgtype": "m.text"},
            "event_id": "$ev2",
            "origin_server_ts": 1234567890,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )

    room = MatrixRoom("!roomid", "alias")

    with patch("matrix.context.Context", autospec=True) as MockContext:
        mock_ctx = MagicMock()
        mock_ctx.body = "!ping"
        mock_ctx.command = bot.commands["ping"]
        MockContext.return_value = mock_ctx

        await bot._process_commands(room, event)

    assert called, "Expected command handler to be called"


@pytest.mark.asyncio
async def test_error_decorator_requires_coroutine(bot):
    with pytest.raises(TypeError):

        @bot.error()
        def sync_handler(error):
            pass


def test_event_decorator_with_unknown_name_raises(bot):
    with pytest.raises(ValueError):

        @bot.event
        async def on_something_unknown(_r, _e):
            pass


def test_event_decorator_requires_coroutine(bot):
    with pytest.raises(TypeError):

        @bot.event
        def not_a_coro(_r, _e):
            pass


def test_event_decorator_event_spec(bot):
    @bot.event(event_spec="on_message")
    async def message_event1(_r, _e):
        pass

    @bot.event(event_spec=RoomMessageText)
    async def message_event2(_r, _e):
        pass


def test_event_decorator_invalid_event_spec(bot):
    with pytest.raises(ValueError):

        @bot.event(event_spec="invalid_event")
        async def message_event(_r, _e):
            pass


def test_command_decorator_requires_coroutine(bot):
    with pytest.raises(TypeError):

        @bot.command()
        def not_async(ctx):
            pass


def test_command_duplicate_raises(bot):
    @bot.command("dup")
    async def cmd1(ctx):
        pass

    with pytest.raises(AlreadyRegisteredError):

        @bot.command("dup")
        async def cmd2(ctx):
            pass


@pytest.mark.asyncio
async def test_run_uses_token():
    bot = Bot("tests/config_fixture_token.yaml")

    bot.client.sync_forever = AsyncMock()
    bot.on_ready = AsyncMock()

    await bot.run()

    assert bot.client.access_token == "abc123"
    bot.on_ready.assert_awaited_once()
    bot.client.sync_forever.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_with_username_and_password(bot):
    bot.client.login = AsyncMock(return_value="login_resp")
    bot.client.sync_forever = AsyncMock()
    bot.on_ready = AsyncMock()

    await bot.run()

    bot.client.login.assert_awaited_once_with("grace1234")
    bot.on_ready.assert_awaited_once()
    bot.client.sync_forever.assert_awaited_once()


def test_start_handles_keyboard_interrupt(caplog):
    bot = Bot("tests/config_fixture.yaml")

    bot.run = AsyncMock(side_effect=KeyboardInterrupt)
    bot.client.close = AsyncMock()

    with caplog.at_level("INFO"):
        bot.start()

    assert "bot interrupted by user" in caplog.text
    bot.client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduled_task_in_scheduler(bot):
    @bot.schedule("* * * * *")
    async def scheduled_task():
        pass

    job_names = list(map(lambda j: j.name, bot.scheduler.scheduler.get_jobs()))
    assert "scheduled_task" in job_names, "Scheduled task not found in scheduler"
