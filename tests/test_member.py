import pytest
from unittest.mock import AsyncMock, Mock

from nio import AsyncClient
from matrix.member import Member, MemberProfile
from matrix.room import Room


@pytest.fixture
def client():
    return AsyncMock(spec=AsyncClient)


@pytest.fixture
def room():
    room = Mock(spec=Room)
    room.room_id = "!room:example.com"
    return room


@pytest.fixture
def member(client):
    return Member("@user:matrix.org", client)


def test_member_user_id__expect_correct_value(member):
    assert member.user_id == "@user:matrix.org"


def test_member_mention__expect_matrix_to_link(member):
    assert (
        member.mention() == "[@user:matrix.org](https://matrix.to/#/@user:matrix.org)"
    )


def test_member_str__expect_mention(member):
    assert str(member) == "[@user:matrix.org](https://matrix.to/#/@user:matrix.org)"


@pytest.mark.asyncio
async def test_get_profile__expect_profile_returned(member, client):
    mock_profile = Mock()
    mock_profile.displayname = "Alice"
    mock_profile.avatar_url = "mxc://matrix.org/avatar"
    mock_profile.other_info = {"chat.commet.profile_status": "Online"}

    client.get_profile = AsyncMock(return_value=mock_profile)

    result = await member.get_profile()

    client.get_profile.assert_awaited_once_with("@user:matrix.org")
    assert result == MemberProfile(
        displayname="Alice",
        avatar_url="mxc://matrix.org/avatar",
        other_info={"chat.commet.profile_status": "Online"},
    )


@pytest.mark.asyncio
async def test_get_profile_empty__expect_none(member, client):
    client.get_profile = AsyncMock(return_value=None)

    result = await member.get_profile()

    assert result is None


@pytest.mark.asyncio
async def test_get_display_name__expect_display_name(member, client):
    response = Mock()
    response.displayname = "Alice"
    client.get_displayname = AsyncMock(return_value=response)

    result = await member.get_display_name()

    client.get_displayname.assert_awaited_once_with("@user:matrix.org")
    assert result == "Alice"


@pytest.mark.asyncio
async def test_get_display_name_empty__expect_none(member, client):
    client.get_displayname = AsyncMock(return_value=None)

    result = await member.get_display_name()

    assert result is None


@pytest.mark.asyncio
async def test_get_avatar_url__expect_http_avatar_url(member, client):
    response = Mock()
    response.avatar_url = "mxc://matrix.org/avatar"

    client.get_avatar = AsyncMock(return_value=response)
    client.mxc_to_http = AsyncMock(return_value="https://matrix.org/avatar")

    result = await member.get_avatar_url()

    client.get_avatar.assert_awaited_once_with("@user:matrix.org")
    client.mxc_to_http.assert_awaited_once_with("mxc://matrix.org/avatar")
    assert result == "https://matrix.org/avatar"


@pytest.mark.asyncio
async def test_get_avatar_url_empty__expect_none(member, client):
    client.get_avatar = AsyncMock(return_value=None)

    result = await member.get_avatar_url()

    client.mxc_to_http.assert_not_awaited()
    assert result is None


@pytest.mark.asyncio
async def test_get_room_power_level__expect_user_power_level(member, room):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 50},
        "users_default": 0,
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    room.get_state_event.assert_awaited_once_with("m.room.power_levels", "")
    assert result == 50


@pytest.mark.asyncio
async def test_get_room_power_level_missing_user__expect_default(member, room):
    response = Mock()
    response.content = {
        "users": {},
        "users_default": 10,
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 10


@pytest.mark.asyncio
async def test_get_room_power_level_missing_content__expect_zero(member, room):
    response = Mock()
    response.content = None
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 0


@pytest.mark.asyncio
async def test_get_room_power_level_missing_event_content_attr__expect_zero(
    member, room
):
    response = object()
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 0


@pytest.mark.asyncio
async def test_get_presence__expect_presence(member, client):
    response = Mock()
    response.presence = "online"
    client.get_presence = AsyncMock(return_value=response)

    result = await member.get_presence()

    client.get_presence.assert_awaited_once_with("@user:matrix.org")
    assert result == "online"


@pytest.mark.asyncio
async def test_get_presence_empty__expect_none(member, client):
    client.get_presence = AsyncMock(return_value=None)

    result = await member.get_presence()

    assert result is None


@pytest.mark.asyncio
async def test_has_room_permission__expect_true(member, client, room):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 50},
        "users_default": 0,
        "ban": 50,
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert room.get_state_event.await_count == 2
    assert result is True


@pytest.mark.asyncio
async def test_has_room_permission__expect_false(member, client, room):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 10},
        "users_default": 0,
        "ban": 50,
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is False


@pytest.mark.asyncio
async def test_has_room_permission_missing_permission__expect_false(
    member, client, room
):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 100},
        "users_default": 0,
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is False


@pytest.mark.asyncio
async def test_has_room_permission_missing_content__expect_false(member, client, room):
    response = Mock()
    response.content = None
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is False


@pytest.mark.asyncio
async def test_has_event_permission__expect_true(member, client, room):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 50},
        "users_default": 0,
        "events": {"m.room.message": 0},
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.message")

    assert room.get_state_event.await_count == 2
    assert result is True


@pytest.mark.asyncio
async def test_has_event_permission__expect_false(member, client, room):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 10},
        "users_default": 0,
        "events": {"m.room.power_levels": 100},
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.power_levels")

    assert result is False


@pytest.mark.asyncio
async def test_has_event_permission_missing_event_level__expect_true(
    member, client, room
):
    response = Mock()
    response.content = {
        "users": {"@user:matrix.org": 0},
        "users_default": 0,
        "events": {},
    }
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.message")

    assert result is True


@pytest.mark.asyncio
async def test_has_event_permission_missing_content__expect_true(member, client, room):
    response = Mock()
    response.content = None
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.message")

    assert result is True
