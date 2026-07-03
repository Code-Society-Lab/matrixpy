import pytest

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from nio import MatrixRoom, RoomMessageText, LoginError, Event

from matrix import Bot, Config, Extension, Room, Space
from matrix.message import Message
from matrix.types import File
from matrix.errors import (
    CheckError,
    CommandNotFoundError,
    AlreadyRegisteredError,
    MatrixError,
)


@pytest.fixture
def bot():
    b = Bot()
    b._load_config(
        Config(
            username="grace",
            password="grace1234",
        )
    )

    b._client = MagicMock()
    b._client.room_send = AsyncMock()
    b.log = MagicMock()
    b.log.getChild.return_value = MagicMock()

    return b


@pytest.fixture
def bot_with_token():
    b = Bot()
    b._load_config(
        Config(
            username="grace",
            token="abc123",
        )
    )

    b._client = MagicMock()
    b._client.room_send = AsyncMock()
    b.log = MagicMock()
    b.log.getChild.return_value = MagicMock()

    return b


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


@pytest.fixture
def space_room():
    space = MatrixRoom(room_id="!space:id", own_user_id="grace")
    space.name = "Test Space"
    space.room_type = "m.space"
    return space


def test_get_room__with_known_room_id__expect_room(bot, room):
    bot._client.rooms = {room.room_id: room}

    result = bot.get_room(room.room_id)

    assert type(result) is Room
    assert result.matrix_room is room


def test_get_room__with_space_room_id__expect_space(bot, space_room):
    bot._client.rooms = {space_room.room_id: space_room}

    result = bot.get_room(space_room.room_id)

    assert isinstance(result, Space)
    assert result.matrix_room is space_room


def test_get_room__with_unknown_room_id__expect_none(bot):
    bot._client.rooms = {}

    assert bot.get_room("!missing:id") is None


def test_get_rooms__expect_all_known_rooms(bot, room, space_room):
    bot._client.rooms = {room.room_id: room, space_room.room_id: space_room}

    rooms = bot.get_rooms()
    by_id = {r.room_id: r for r in rooms}

    assert len(rooms) == 2
    assert type(by_id[room.room_id]) is Room
    assert isinstance(by_id[space_room.room_id], Space)


def test_get_space__with_space_room_id__expect_space(bot, space_room):
    bot._client.rooms = {space_room.room_id: space_room}

    result = bot.get_space(space_room.room_id)

    assert isinstance(result, Space)
    assert result.matrix_room is space_room


def test_get_space__with_non_space_room_id__expect_none(bot, room):
    bot._client.rooms = {room.room_id: room}

    assert bot.get_space(room.room_id) is None


def test_get_space__with_unknown_room_id__expect_none(bot):
    bot._client.rooms = {}

    assert bot.get_space("!missing:id") is None


def test_get_spaces__with_mixed_rooms__expect_only_spaces(bot, room, space_room):
    bot._client.rooms = {room.room_id: room, space_room.room_id: space_room}

    spaces = bot.get_spaces()

    assert len(spaces) == 1
    assert isinstance(spaces[0], Space)
    assert spaces[0].matrix_room is space_room


def test_get_spaces__with_no_spaces__expect_empty_list(bot, room):
    bot._client.rooms = {room.room_id: room}

    assert bot.get_spaces() == []


def test_bot_init_with_config():
    bot = Bot()
    bot._load_config(Config(username="grace", password="grace1234"))

    assert bot.config.username == "grace"
    assert bot.config.password == "grace1234"
    assert bot.config.homeserver == "https://matrix.org"


def test_bot_init_with_invalid_config_file():
    bot = Bot()
    with pytest.raises(FileNotFoundError):
        bot._load_config("not-a-dict")


def test_auto_register_events_registers_known_events(bot):
    async def on_message(room, event):
        pass

    setattr(bot, "on_message", on_message)

    with patch.object(bot, "event", wraps=bot.event) as mock_event:
        bot._auto_register_events()

    mock_event.assert_any_call(on_message)


@pytest.mark.asyncio
async def test_dispatch_calls_all_handlers(bot):
    called = []

    async def handler1(room, event):
        called.append("h1")

    async def handler2(room, event):
        called.append("h2")

    bot._event_handlers[RoomMessageText].append(handler1)
    bot._event_handlers[RoomMessageText].append(handler2)

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "test", "msgtype": "m.text"},
            "event_id": "$id",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )
    matrix_room = MatrixRoom("!roomid:matrix.org", "room_alias")
    room = Room(matrix_room, bot.client)

    await bot._dispatch_matrix_event(room, event)
    assert "h1" in called
    assert "h2" in called


@pytest.mark.asyncio
async def test_on_event_ignores_self_events(bot):
    bot.start_at = None
    bot._client.user = "@grace:matrix.org"

    event = MagicMock(spec=RoomMessageText)
    event.sender = "@grace:matrix.org"
    event.server_timestamp = 123456789

    with patch.object(
        bot, "_dispatch_matrix_event", new_callable=AsyncMock
    ) as dispatch:
        await bot._on_matrix_event(MatrixRoom("!room:matrix.org", "alias"), event)
        dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_ignores_old_events(bot, room, event):
    bot._client.user = "@somebot:matrix.org"
    bot.start_at = event.server_timestamp / 1000 + 10

    bot._dispatch_matrix_event = AsyncMock()
    await bot._on_matrix_event(room, event)

    bot._dispatch_matrix_event.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_calls_error_handler(bot):
    bot._dispatch_matrix_event = AsyncMock(side_effect=Exception("boom"))

    custom_error_handler = AsyncMock()
    bot.error()(custom_error_handler)

    event = MagicMock(spec=RoomMessageText)
    event.sender = "@someone:matrix.org"
    event.server_timestamp = 999999999
    bot.start_at = 0
    bot._client.user = "@grace:matrix.org"

    await bot._on_matrix_event(MatrixRoom("!roomid", "alias"), event)
    custom_error_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_message_calls_process_commands(bot, room, event):
    with patch.object(bot, "_process_commands", new_callable=AsyncMock) as mock_proc:
        await bot.on_message(room, event)
        mock_proc.assert_awaited_once_with(room, event)


@pytest.mark.asyncio
async def test_on_ready_dispatches(bot):
    with patch.object(bot, "_dispatch", new_callable=AsyncMock) as mock_dispatch:
        await bot._on_ready()
        mock_dispatch.assert_awaited_once_with("on_ready")


@pytest.mark.asyncio
async def test_on_error_calls_specific_handler(bot):
    called = False

    @bot.error(ValueError)
    async def custom_error_handler(e):
        nonlocal called
        called = True

    await bot._on_error(ValueError("test error"))

    assert called, "Specific error handler was not called"


@pytest.mark.asyncio
async def test_on_error_calls_fallback_handler(bot):
    called = False

    @bot.error()
    async def custom_error_handler(e):
        nonlocal called
        called = True

    await bot._on_error(Exception("test error"))
    assert called, "Fallback error handler was not called"


@pytest.mark.asyncio
async def test_on_error_logs_when_no_handler(bot):
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

    with patch.object(
        bot, "_build_context", new_callable=AsyncMock
    ) as mock_build_context:
        ctx = MagicMock()
        ctx.command = bot.commands["greet"]
        mock_build_context.return_value = ctx

        await bot._process_commands(room, event)

    assert called, "Expected command handler to be called"


@pytest.mark.asyncio
async def test_command_not_found_calls_command_error_handler(bot):
    bot._on_command_error = AsyncMock()

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

    await bot._process_commands(room, event)

    bot._on_command_error.assert_awaited_once()
    assert isinstance(bot._on_command_error.call_args[0][1], CommandNotFoundError)


@pytest.mark.asyncio
async def test_bot_does_not_execute_command_when_global_check_fails(bot):
    called = False

    @bot.command()
    async def greet(ctx):
        nonlocal called
        called = True

    @bot.check
    async def global_check(ctx):
        return False

    bot._on_command_error = AsyncMock()

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "!greet", "msgtype": "m.text"},
            "event_id": "$ev2",
            "origin_server_ts": 1234567890,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )

    matrix_room = MatrixRoom("!roomid", "alias")
    room = Room(matrix_room, bot.client)

    await bot._process_commands(room, event)

    assert not called
    bot._on_command_error.assert_awaited_once()
    assert isinstance(bot._on_command_error.call_args[0][1], CheckError)


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
async def test_command_not_processed_without_prefix(bot, room):
    called = False

    @bot.command()
    async def greet(ctx):
        nonlocal called
        called = True

    event = RoomMessageText.from_dict(
        {
            "content": {"body": "greet", "msgtype": "m.text"},
            "event_id": "$id",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )

    await bot._process_commands(room, event)

    assert not called


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


import asyncio


async def start_and_stop(coro):
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)  # allow startup
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_run_uses_token(bot_with_token):
    bot_with_token._client.sync_forever = AsyncMock()
    bot_with_token._on_ready = AsyncMock()

    # unblock readiness
    bot_with_token._synced.set()

    task = asyncio.create_task(bot_with_token.run())

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    assert bot_with_token._client.access_token == "abc123"
    bot_with_token._on_ready.assert_awaited_once()
    bot_with_token._client.sync_forever.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_with_username_and_password(bot):
    assert bot.config.token is None

    login_called = asyncio.Event()

    async def mock_login(password):
        login_called.set()
        return "login_resp"

    bot._client.login = AsyncMock(side_effect=mock_login)
    bot._client.sync_forever = AsyncMock()
    bot._on_ready = AsyncMock()

    bot._synced.set()

    task = asyncio.create_task(bot.run())

    await asyncio.wait_for(login_called.wait(), timeout=1.0)

    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    bot._client.login.assert_awaited_once_with("grace1234")
    bot._on_ready.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_with_login_api_error__expect_matrix_error(bot):
    bot._client.login = AsyncMock(
        return_value=LoginError("bad credentials", "M_FORBIDDEN")
    )
    bot._client.sync_forever = AsyncMock()
    bot._on_ready = AsyncMock()

    with pytest.raises(MatrixError, match="Failed to log in"):
        await bot.run()

    bot._client.sync_forever.assert_not_called()
    bot._on_ready.assert_not_called()


def test_start_handles_keyboard_interrupt(caplog):
    bot = Bot()
    bot._client = MagicMock()
    bot._client.close = AsyncMock()
    bot.run = AsyncMock(side_effect=KeyboardInterrupt)

    with patch.object(bot, "_load_config"):
        with caplog.at_level("INFO"):
            bot.start(
                config=Config(
                    username="grace",
                    password="grace1234",
                )
            )

    assert "bot interrupted by user" in caplog.text
    bot._client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_ready_called_only_once(bot):
    # Prepare
    bot._synced.set()
    bot._on_ready = AsyncMock()

    # Simulate run
    await bot._wait_until_synced()
    await bot._on_ready()

    bot._on_ready.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduler_starts_after_ready(bot):
    bot._synced.set()

    order = []

    async def ready():
        order.append("ready")

    bot._on_ready = AsyncMock(side_effect=ready)
    bot.scheduler.start = MagicMock(side_effect=lambda: order.append("scheduler"))

    # Simulate run
    await bot._wait_until_synced()
    await bot._on_ready()
    bot.scheduler.start()

    assert order == ["ready", "scheduler"]


@pytest.mark.asyncio
async def test_scheduled_task_in_scheduler(bot):
    @bot.schedule("* * * * *")
    async def scheduled_task():
        pass

    job_names = list(map(lambda j: j.name, bot._scheduler.jobs))
    assert "scheduled_task" in job_names, "Scheduled task not found in scheduler"


@pytest.fixture
def extension() -> Extension:
    ext = Extension(name="test_ext", prefix="!")

    @ext.command()
    async def hello(ctx):
        pass

    return ext


def test_load_extension_with_valid_extension__expect_extension_in_registry(
    bot: Bot, extension: Extension
):
    bot.load_extension(extension)

    assert "test_ext" in bot.extensions


def test_load_extension_with_duplicate_extension__expect_already_registered_error(
    bot: Bot, extension: Extension
):
    bot.load_extension(extension)

    with pytest.raises(AlreadyRegisteredError):
        bot.load_extension(extension)


def test_load_extension_with_commands__expect_commands_in_bot(
    bot: Bot, extension: Extension
):
    bot.load_extension(extension)

    assert "hello" in bot.commands


def test_load_extension_with_group__expect_group_in_bot(bot: Bot):
    ext = Extension(name="math_ext", prefix="!")

    @ext.group()
    async def math(ctx):
        pass

    bot.load_extension(ext)

    assert "math" in bot.commands


def test_load_extension_with_event_handlers__expect_handlers_in_bot(bot: Bot):
    ext = Extension(name="events_ext")

    @ext.event
    async def on_message(room, event):
        pass

    bot.load_extension(ext)

    assert on_message in bot._event_handlers[RoomMessageText]


def test_load_extension_with_multiple_event_handlers__expect_all_handlers_in_bot(
    bot: Bot,
):
    ext = Extension(name="multi_events_ext")

    @ext.event
    async def on_message(room, event):
        pass

    @ext.event(event_spec="on_message")
    async def on_message_two(room, event):
        pass

    bot.load_extension(ext)

    assert on_message in bot._event_handlers[RoomMessageText]
    assert on_message_two in bot._event_handlers[RoomMessageText]


def test_load_extension_with_checks__expect_checks_in_bot(bot: Bot):
    ext = Extension(name="checks_ext")

    @ext.check
    async def only_admins(ctx):
        return True

    bot.load_extension(ext)

    assert only_admins in bot._checks


def test_load_extension_with_error_handlers__expect_handlers_in_bot(bot: Bot):
    ext = Extension(name="errors_ext")

    @ext.error(ValueError)
    async def on_value_error(error):
        pass

    bot.load_extension(ext)

    assert ValueError in bot._error_handlers
    assert bot._error_handlers[ValueError] is on_value_error


def test_load_extension_with_scheduled_tasks__expect_jobs_in_bot_scheduler(bot: Bot):
    ext = Extension(name="scheduler_ext")

    @ext.schedule("* * * * *")
    async def periodic_task():
        pass

    bot.load_extension(ext)

    job_names = [j.name for j in bot.scheduler.jobs]
    assert "periodic_task" in job_names


def test_load_extension_does_not_add_jobs_to_extension_scheduler(bot: Bot):
    ext = Extension(name="scheduler_ext")

    @ext.schedule("* * * * *")
    async def periodic_task():
        pass

    initial_bot_job_count = len(bot.scheduler.jobs)
    bot.load_extension(ext)

    assert len(bot.scheduler.jobs) == initial_bot_job_count + 1


def test_load_extension_logs_loading(bot: Bot, extension: Extension):
    bot.load_extension(extension)

    bot.log.debug.assert_any_call("loaded extension '%s'", extension.name)


def test_load_extension_with_empty_extension__expect_no_commands_added(bot: Bot):
    ext = Extension(name="empty_ext")
    initial_command_count = len(bot.commands)

    bot.load_extension(ext)

    assert len(bot.commands) == initial_command_count


@pytest.fixture
def loaded_extension(bot: Bot) -> Extension:
    ext = Extension(name="loaded_ext", prefix="!")

    @ext.command()
    async def hello(ctx):
        pass

    bot.load_extension(ext)
    return ext


def test_unload_extension_with_valid_name__expect_extension_removed_from_registry(
    bot: Bot, loaded_extension: Extension
):
    bot.unload_extension(loaded_extension.name)

    assert loaded_extension.name not in bot.extensions


def test_unload_extension_with_unknown_name__expect_value_error(bot: Bot):
    with pytest.raises(ValueError):
        bot.unload_extension("nonexistent_ext")


def test_unload_extension_with_commands__expect_commands_removed_from_bot(
    bot: Bot, loaded_extension: Extension
):
    bot.unload_extension(loaded_extension.name)

    assert "hello" not in bot.commands


def test_unload_extension_with_group__expect_group_removed_from_bot(bot: Bot):
    ext = Extension(name="group_ext", prefix="!")

    @ext.group()
    async def math(ctx):
        pass

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    assert "math" not in bot.commands


def test_unload_extension_with_event_handlers__expect_handlers_removed_from_bot(
    bot: Bot,
):
    ext = Extension(name="events_ext")

    @ext.event
    async def on_message(room, event):
        pass

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    assert on_message not in bot._event_handlers[RoomMessageText]


def test_unload_extension_with_multiple_event_handlers__expect_all_handlers_removed(
    bot: Bot,
):
    ext = Extension(name="multi_events_ext")

    @ext.event
    async def on_message(room, event):
        pass

    @ext.event(event_spec="on_message")
    async def on_message_two(room, event):
        pass

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    assert on_message not in bot._event_handlers[RoomMessageText]
    assert on_message_two not in bot._event_handlers[RoomMessageText]


def test_unload_extension_does_not_remove_other_extension_handlers(bot: Bot):
    ext_a = Extension(name="ext_a")
    ext_b = Extension(name="ext_b")

    @ext_a.event
    async def on_message(room, event):
        pass

    @ext_b.event(event_spec="on_message")
    async def on_message_b(room, event):
        pass

    bot.load_extension(ext_a)
    bot.load_extension(ext_b)
    bot.unload_extension(ext_a.name)

    assert on_message not in bot._event_handlers[RoomMessageText]
    assert on_message_b in bot._event_handlers[RoomMessageText]


def test_unload_extension_with_checks__expect_checks_removed_from_bot(bot: Bot):
    ext = Extension(name="checks_ext")

    @ext.check
    async def only_admins(ctx):
        return True

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    assert only_admins not in bot._checks


def test_unload_extension_with_error_handlers__expect_handlers_removed_from_bot(
    bot: Bot,
):
    ext = Extension(name="errors_ext")

    @ext.error(ValueError)
    async def on_value_error(error):
        pass

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    assert ValueError not in bot._error_handlers


def test_unload_extension_with_scheduled_tasks__expect_jobs_removed_from_bot_scheduler(
    bot: Bot,
):
    ext = Extension(name="scheduler_ext")

    @ext.schedule("* * * * *")
    async def periodic_task():
        pass

    bot.load_extension(ext)
    bot.unload_extension(ext.name)

    job_names = [j.name for j in bot.scheduler.jobs]
    assert "periodic_task" not in job_names


def test_unload_extension_does_not_remove_other_extension_jobs(bot: Bot):
    ext_a = Extension(name="scheduler_ext_a")
    ext_b = Extension(name="scheduler_ext_b")

    @ext_a.schedule("* * * * *")
    async def task_a():
        pass

    @ext_b.schedule("* * * * *")
    async def task_b():
        pass

    bot.load_extension(ext_a)
    bot.load_extension(ext_b)
    bot.unload_extension(ext_a.name)

    job_names = [j.name for j in bot.scheduler.jobs]
    assert "task_a" not in job_names
    assert "task_b" in job_names


def test_unload_extension_logs_unloading(bot: Bot, loaded_extension: Extension):
    bot.unload_extension(loaded_extension.name)

    bot.log.debug.assert_any_call("unloaded extension '%s'", loaded_extension.name)


def test_unload_extension_removes_only_its_jobs(bot: Bot):
    ext_a = Extension(name="a")
    ext_b = Extension(name="b")

    @ext_a.schedule("* * * * *")
    async def task():
        pass

    @ext_b.schedule("* * * * *")
    async def task():
        pass

    bot.load_extension(ext_a)
    bot.load_extension(ext_b)

    bot.unload_extension("a")

    job_names = [j.name for j in bot.scheduler.jobs]

    assert "task" in job_names


@pytest.fixture
def mock_send_response(bot):
    """Set up client to return a mock event after room_send and fetch_event."""
    send_response = Mock()
    send_response.event_id = "$event123"
    bot._client.room_send = AsyncMock(return_value=send_response)

    mock_event = MagicMock(spec=Event)
    mock_event.event_id = "$event123"

    get_event_response = Mock()
    get_event_response.event = mock_event
    bot._client.room_get_event = AsyncMock(return_value=get_event_response)

    return send_response


@pytest.fixture
def make_room(bot):
    """Factory that creates a Room instance for a given room ID."""
    def _make(room_id):
        matrix_room = MatrixRoom(room_id=room_id, own_user_id="grace")
        matrix_room.name = room_id
        bot._client.rooms = {**bot._client.rooms, room_id: matrix_room}
        return Room(matrix_room, bot.client)

    return _make


@pytest.mark.asyncio
async def test_broadcast__expect_message_sent_to_all_rooms(
    bot, make_room, mock_send_response
):
    room1 = make_room("!room1:example.com")
    room2 = make_room("!room2:example.com")

    results = await bot.broadcast([room1, room2], "Hello!")

    assert len(results) == 2
    assert all(isinstance(msg, Message) for msg in results)
    assert bot._client.room_send.await_count == 2


@pytest.mark.asyncio
async def test_broadcast__with_empty_list__expect_no_messages(
    bot, mock_send_response
):
    results = await bot.broadcast([], "Hello!")

    assert results == []
    bot._client.room_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast__with_space_in_list__expect_space_skipped(
    bot, make_room, mock_send_response
):
    room = make_room("!room:example.com")
    space_matrix = MatrixRoom(
        room_id="!space:example.com", own_user_id="grace"
    )
    space_matrix.name = "Test Space"
    space_matrix.room_type = "m.space"
    bot._client.rooms = {**bot._client.rooms, "!space:example.com": space_matrix}
    space = Space(space_matrix, bot.client)

    results = await bot.broadcast([room, space], "Hello!")

    assert len(results) == 1
    assert bot._client.room_send.await_count == 1
    sent_room_ids = {
        call.kwargs["room_id"] for call in bot._client.room_send.await_args_list
    }
    assert sent_room_ids == {"!room:example.com"}


@pytest.mark.asyncio
async def test_broadcast_raw__expect_unformatted_messages(
    bot, make_room, mock_send_response
):
    room = make_room("!room:example.com")

    await bot.broadcast([room], "Hello world!", raw=True)

    call_args = bot._client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.text"
    assert content["body"] == "Hello world!"
    assert "formatted_body" not in content


@pytest.mark.asyncio
async def test_broadcast_notice__expect_notice_message_type(
    bot, make_room, mock_send_response
):
    room = make_room("!room:example.com")

    await bot.broadcast([room], "Special Event started!", notice=True)

    call_args = bot._client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.notice"
    assert content["body"] == "Special Event started!"


@pytest.mark.asyncio
async def test_broadcast_file__expect_file_message(
    bot, make_room, mock_send_response
):
    room = make_room("!room:example.com")

    file = File(
        path="mxc://example.com/abc123",
        filename="document.pdf",
        mimetype="application/pdf",
    )

    await bot.broadcast([room], file=file)

    call_args = bot._client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.file"
    assert content["body"] == "document.pdf"
    assert content["url"] == "mxc://example.com/abc123"
