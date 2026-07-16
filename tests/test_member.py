import pytest
from unittest.mock import AsyncMock, Mock

from nio import (
    AsyncClient,
    ErrorResponse,
    PresenceGetResponse,
    ProfileGetAvatarResponse,
    ProfileGetDisplayNameResponse,
    ProfileGetResponse,
    RoomGetStateEventResponse,
)
from matrix.member import Member, MemberProfile
from matrix.room import Room
from matrix.errors import MatrixError


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


def power_levels_response(content):
    return RoomGetStateEventResponse(
        content=content,
        event_type="m.room.power_levels",
        state_key="",
        room_id="!room:example.com",
    )


def test_member_user_id__expect_configured_user_id(member):
    assert member.user_id == "@user:matrix.org"


def test_member_mention__expect_markdown_matrix_to_link(member):
    assert (
        member.mention() == "[@user:matrix.org](https://matrix.to/#/@user:matrix.org)"
    )


def test_member_str__expect_same_value_as_mention(member):
    assert str(member) == member.mention()


@pytest.mark.asyncio
async def test_get_profile__with_profile_response__expect_member_profile(
    member, client
):
    response = ProfileGetResponse(
        displayname="Alice",
        avatar_url="mxc://matrix.org/avatar",
        other_info={"chat.commet.profile_status": "Online"},
    )
    client.get_profile = AsyncMock(return_value=response)

    result = await member.get_profile()

    client.get_profile.assert_awaited_once_with("@user:matrix.org")
    assert result == MemberProfile(
        displayname="Alice",
        avatar_url="mxc://matrix.org/avatar",
        other_info={"chat.commet.profile_status": "Online"},
    )


@pytest.mark.asyncio
async def test_get_display_name__with_display_name__expect_value(member, client):
    response = ProfileGetDisplayNameResponse(displayname="Alice")
    client.get_displayname = AsyncMock(return_value=response)

    result = await member.get_display_name()

    client.get_displayname.assert_awaited_once_with("@user:matrix.org")
    assert result == "Alice"


@pytest.mark.asyncio
async def test_get_display_name__without_display_name__expect_none(member, client):
    client.get_displayname = AsyncMock(return_value=ProfileGetDisplayNameResponse())

    result = await member.get_display_name()

    assert result is None


@pytest.mark.asyncio
async def test_get_display_name__when_client_returns_none__expect_none(member, client):
    response = ProfileGetDisplayNameResponse(displayname=None)
    client.get_displayname = AsyncMock(return_value=response)

    result = await member.get_display_name()

    assert result is None


@pytest.mark.asyncio
async def test_get_avatar_url__with_mxc_avatar__expect_http_url(member, client):
    response = ProfileGetAvatarResponse(avatar_url="mxc://matrix.org/avatar")
    client.get_avatar = AsyncMock(return_value=response)
    client.mxc_to_http = AsyncMock(return_value="https://matrix.org/avatar")

    result = await member.get_avatar_url()

    client.get_avatar.assert_awaited_once_with("@user:matrix.org")
    client.mxc_to_http.assert_awaited_once_with("mxc://matrix.org/avatar")
    assert result == "https://matrix.org/avatar"


@pytest.mark.asyncio
async def test_get_avatar_url__when_client_returns_none__expect_none(member, client):
    response = ProfileGetAvatarResponse(avatar_url=None)
    client.get_avatar = AsyncMock(return_value=response)
    result = await member.get_avatar_url()

    assert result is None


@pytest.mark.asyncio
async def test_get_room_power_level__expect_user_power_level(member, room):
    response = power_levels_response(
        {"users": {"@user:matrix.org": 50}, "users_default": 0}
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    room.get_state_event.assert_awaited_once_with("m.room.power_levels", "")
    assert result == 50


@pytest.mark.asyncio
async def test_get_room_power_level__when_user_not_listed__expect_users_default(
    member, room
):
    response = power_levels_response({"users": {}, "users_default": 10})
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 10


@pytest.mark.asyncio
async def test_get_room_power_level__when_content_empty__expect_zero(member, room):
    response = power_levels_response({})
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 0


@pytest.mark.asyncio
async def test_get_room_power_level__when_users_is_empty__expect_zero(member, room):
    response = power_levels_response({"users": {}, "users_default": 0})
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.get_room_power_level(room)

    assert result == 0


@pytest.mark.asyncio
async def test_get_presence__with_all_values__expect_all_values(member, client):
    response = PresenceGetResponse(
        user_id="@user:matrix.org",
        presence="online",
        last_active_ago=1000,
        currently_active=True,
        status_msg="Available",
    )
    client.get_presence = AsyncMock(return_value=response)

    result = await member.get_presence()

    client.get_presence.assert_awaited_once_with("@user:matrix.org")
    assert result.user_id == "@user:matrix.org"
    assert result.presence == "online"
    assert result.last_active_ago == 1000
    assert result.currently_active is True
    assert result.status_msg == "Available"


@pytest.mark.asyncio
async def test_get_presence__without_optional_values__expect_none(member, client):
    response = PresenceGetResponse(
        user_id="@user:matrix.org",
        presence="online",
        last_active_ago=None,
        currently_active=None,
        status_msg=None,
    )
    client.get_presence = AsyncMock(return_value=response)

    result = await member.get_presence()

    client.get_presence.assert_awaited_once_with("@user:matrix.org")
    assert result.user_id == "@user:matrix.org"
    assert result.presence == "online"
    assert result.last_active_ago is None
    assert result.currently_active is None
    assert result.status_msg is None


@pytest.mark.asyncio
async def test_has_room_permission__with_user_level_meeting_requirement__expect_true(
    member, room
):
    response = power_levels_response(
        {
            "users": {"@user:matrix.org": 50},
            "users_default": 0,
            "ban": 50,
        }
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is True


@pytest.mark.asyncio
async def test_has_room_permission__with_user_level_too_low__expect_false(member, room):
    response = power_levels_response(
        {
            "users": {"@user:matrix.org": 10},
            "users_default": 0,
            "ban": 50,
        }
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is False


@pytest.mark.asyncio
async def test_has_room_permission__when_permission_not_defined__expect_false(
    member, room
):
    response = power_levels_response(
        {"users": {"@user:matrix.org": 100}, "users_default": 0}
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_room_permission(room, "ban")

    assert result is False


@pytest.mark.asyncio
async def test_has_event_permission__with_user_level_meeting_requirement__expect_true(
    member, room
):
    response = power_levels_response(
        {
            "users": {"@user:matrix.org": 50},
            "users_default": 0,
            "events": {"m.room.message": 0},
        }
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.message")

    assert room.get_state_event.await_count == 2
    assert result is True


@pytest.mark.asyncio
async def test_has_event_permission__with_user_level_too_low__expect_false(
    member, room
):
    response = power_levels_response(
        {
            "users": {"@user:matrix.org": 10},
            "users_default": 0,
            "events": {"m.room.power_levels": 100},
        }
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.power_levels")

    assert result is False


@pytest.mark.asyncio
async def test_has_event_permission__when_event_level_not_defined__expect_false(
    member, room
):
    response = power_levels_response(
        {
            "users": {"@user:matrix.org": 0},
            "users_default": 0,
            "events": {},
        }
    )
    room.get_state_event = AsyncMock(return_value=response)

    result = await member.has_event_permission(room, "m.room.message")

    assert result is False


@pytest.mark.asyncio
async def test_get_profile__when_client_returns_error__expect_matrix_error(
    member, client
):
    client.get_profile = AsyncMock(return_value=ErrorResponse("not found"))

    with pytest.raises(MatrixError, match="Failed to get profile"):
        await member.get_profile()


@pytest.mark.asyncio
async def test_has_room_permission__when_state_event_fails__expect_matrix_error(
    member, room
):
    room.get_state_event = AsyncMock(
        side_effect=MatrixError("Failed to get state event for room !room:example.com")
    )

    with pytest.raises(MatrixError):
        await member.has_room_permission(room, "ban")
