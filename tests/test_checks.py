import pytest

from unittest.mock import AsyncMock, Mock
from nio import MatrixRoom, RoomMessageText, AsyncClient, PowerLevels

from matrix.checks import is_admin, is_moderator
from matrix.command import Command
from matrix.context import Context
from matrix.errors import CheckError
from matrix.room import Room


@pytest.fixture
def client():
    return AsyncMock(spec=AsyncClient)


@pytest.fixture
def bot(client):
    bot = Mock()
    bot.prefix = "!"
    bot.client = client
    bot.log = Mock()
    bot.log.getChild = Mock(return_value=Mock())
    return bot


def make_event(sender: str) -> RoomMessageText:
    return RoomMessageText.from_dict(
        {
            "content": {"body": "!restricted", "msgtype": "m.text"},
            "event_id": "$event123",
            "origin_server_ts": 123456,
            "sender": sender,
            "type": "m.room.message",
        }
    )


def make_context(bot, client, sender: str, level: int) -> Context:
    """Builds a real Context whose room reports `level` as the sender's power level."""
    matrix_room = Mock(spec=MatrixRoom)
    matrix_room.room_id = "!room:example.com"
    matrix_room.power_levels = PowerLevels(users={sender: level})

    room = Room(matrix_room, client)
    return Context(bot, room, make_event(sender))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "level, expected",
    [
        (100, True),
        (99, False),
        (50, False),
        (0, False),
    ],
)
async def test_is_admin_check__respects_power_level_boundaries(
    bot, client, level, expected
):
    async def my_command(ctx):
        pass

    cmd = Command(my_command)
    is_admin()(cmd)

    check = cmd.checks[-1]
    ctx = make_context(bot, client, "@user:example.com", level)

    assert await check(ctx) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "level, expected",
    [
        (100, True),
        (50, True),
        (49, False),
        (0, False),
    ],
)
async def test_is_moderator_check__respects_power_level_boundaries(
    bot, client, level, expected
):
    async def my_command(ctx):
        pass

    cmd = Command(my_command)
    is_moderator()(cmd)

    check = cmd.checks[-1]
    ctx = make_context(bot, client, "@user:example.com", level)

    assert await check(ctx) is expected


def test_is_admin__returns_the_same_command():
    async def my_command(ctx):
        pass

    cmd = Command(my_command)
    assert is_admin()(cmd) is cmd


def test_is_moderator__returns_the_same_command():
    async def my_command(ctx):
        pass

    cmd = Command(my_command)
    assert is_moderator()(cmd) is cmd


@pytest.mark.asyncio
async def test_is_admin__raises_check_error_when_not_admin(bot, client):
    called = False

    async def restricted(ctx):
        nonlocal called
        called = True

    cmd = Command(restricted)
    is_admin()(cmd)

    caught: list[Exception] = []

    @cmd.error(CheckError)
    async def on_check_error(ctx, error):
        caught.append(error)

    ctx = make_context(bot, client, "@user:example.com", 0)
    await cmd(ctx)

    assert called is False
    assert len(caught) == 1
    assert isinstance(caught[0], CheckError)


@pytest.mark.asyncio
async def test_is_moderator__allows_command_when_moderator(bot, client):
    called = False

    async def restricted(ctx):
        nonlocal called
        called = True

    cmd = Command(restricted)
    is_moderator()(cmd)

    ctx = make_context(bot, client, "@mod:example.com", 50)
    await cmd(ctx)

    assert called is True
