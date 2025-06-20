import pytest
from unittest.mock import AsyncMock
from matrix.errors import MatrixError
from matrix.room import Room


@pytest.fixture
def room_default():
    bot = AsyncMock()
    room_id = "!room:id"
    return Room(room_id, bot)


@pytest.fixture
def message():
    message_mock = AsyncMock()
    message_mock.send = AsyncMock()
    return message_mock


@pytest.mark.asyncio
async def test_send_message_room_success(room_default, message):
    message.send.return_value = None

    room_default.bot.client.room_send = message.send

    msg_to_send = "Hello, world!"

    await room_default.send(msg_to_send)
    message.send.assert_awaited_once_with(
        room_id=room_default.room_id,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": msg_to_send,
            "format": "org.matrix.custom.html",
            "formatted_body": f"<p>{msg_to_send}</p>",
        },
    )


@pytest.mark.asyncio
async def test_send_message_room_failure(room_default, message):
    message.send.side_effect = Exception("Failed to send message")

    room_default.bot.client.room_send = message.send

    with pytest.raises(MatrixError, match="Failed to send message"):
        await room_default.send("Hello, world!")


@pytest.mark.asyncio
async def test_invite_user_success(room_default):
    room_default.bot.client.room_invite = AsyncMock()
    room_default.bot.client.room_invite.return_value = None

    await room_default.invite_user("@user:matrix.org")
    room_default.bot.client.room_invite.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org"
    )


@pytest.mark.asyncio
async def test_invite_user_failure(room_default):
    room_default.bot.client.room_invite = AsyncMock()
    room_default.bot.client.room_invite.side_effect = Exception("Failed to invite user")

    with pytest.raises(MatrixError, match="Failed to invite user"):
        await room_default.invite_user("@user:matrix.org")


@pytest.mark.asyncio
async def test_ban_user_success_without_reason(room_default):
    room_default.bot.client.room_ban = AsyncMock()
    room_default.bot.client.room_ban.return_value = None

    await room_default.ban_user("!room:id", "@user:matrix.org")
    room_default.bot.client.room_ban.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org", reason=None
    )


@pytest.mark.asyncio
async def test_ban_user_success_with_reason(room_default):
    room_default.bot.client.room_ban = AsyncMock()
    room_default.bot.client.room_ban.return_value = None

    await room_default.ban_user("!room:id", "@user:matrix.org", "Test Ban")
    room_default.bot.client.room_ban.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org", reason="Test Ban"
    )


@pytest.mark.asyncio
async def test_ban_user_failure(room_default):
    room_default.bot.client.room_ban = AsyncMock()
    room_default.bot.client.room_ban.side_effect = Exception("Failed to ban user")

    with pytest.raises(MatrixError, match="Failed to ban user"):
        await room_default.ban_user("!room:id", "@user:matrix.org")


@pytest.mark.asyncio
async def test_unban_user_success(room_default):
    room_default.bot.client.room_unban = AsyncMock()
    room_default.bot.client.room_unban.return_value = None

    await room_default.unban_user("!room:id", "@user:matrix.org")
    room_default.bot.client.room_unban.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org"
    )


@pytest.mark.asyncio
async def test_unban_user_failure(room_default):
    room_default.bot.client.room_unban = AsyncMock()
    room_default.bot.client.room_unban.side_effect = Exception("Failed to unban user")

    with pytest.raises(MatrixError, match="Failed to unban user"):
        await room_default.unban_user("!room:id", "@user:matrix.org")


@pytest.mark.asyncio
async def test_kick_user_success_without_reason(room_default):
    room_default.bot.client.room_kick = AsyncMock()
    room_default.bot.client.room_kick.return_value = None

    await room_default.kick_user("!room:id", "@user:matrix.org")
    room_default.bot.client.room_kick.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org", reason=None
    )


@pytest.mark.asyncio
async def test_kick_user_success_with_reason(room_default):
    room_default.bot.client.room_kick = AsyncMock()
    room_default.bot.client.room_kick.return_value = None

    await room_default.kick_user("!room:id", "@user:matrix.org", "Test Kick")
    room_default.bot.client.room_kick.assert_awaited_once_with(
        room_id=room_default.room_id, user_id="@user:matrix.org", reason="Test Kick"
    )


@pytest.mark.asyncio
async def test_kick_user_failure(room_default):
    room_default.bot.client.room_kick = AsyncMock()
    room_default.bot.client.room_kick.side_effect = Exception("Failed to kick user")

    with pytest.raises(MatrixError, match="Failed to kick user"):
        await room_default.kick_user("!room:id", "@user:matrix.org")
