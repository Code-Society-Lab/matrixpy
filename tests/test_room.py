import pytest
from unittest.mock import AsyncMock, Mock
from nio import MatrixRoom
from matrix.errors import MatrixError
from matrix.room import Room
from matrix.message import Message


@pytest.fixture
def matrix_room():
    room = Mock(spec=MatrixRoom)
    room.room_id = "!room:example.com"
    room.name = "Test Room"
    room.display_name = "Test Room"
    room.topic = "A test room"
    room.member_count = 5
    room.encrypted = False
    return room


@pytest.fixture
def client():
    client = AsyncMock()
    return client


@pytest.fixture
def room(matrix_room, client):
    return Room(matrix_room, client)


@pytest.mark.asyncio
async def test_send_markdown__expect_formatted_message(room, client):
    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    msg = await room.send("Hello **world**!")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    assert call_args.kwargs["room_id"] == "!room:example.com"
    assert call_args.kwargs["message_type"] == "m.room.message"
    assert call_args.kwargs["content"]["msgtype"] == "m.text"
    assert call_args.kwargs["content"]["body"] == "Hello **world**!"
    assert "formatted_body" in call_args.kwargs["content"]
    assert isinstance(msg, Message)
    assert msg.id == "$event123"


@pytest.mark.asyncio
async def test_send_raw__expect_unformatted_message(room, client):
    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    await room.send("Hello world!", raw=True)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.text"
    assert content["body"] == "Hello world!"
    assert "formatted_body" not in content


@pytest.mark.asyncio
async def test_send_notice__expect_notice_message_type(room, client):
    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    await room.send("Bot starting up...", notice=True)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.notice"
    assert content["body"] == "Bot starting up..."


@pytest.mark.asyncio
async def test_send_text_with_reply_to__expect_threaded_reply(room, client):
    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    await room.send_text("Replying!", reply_to="$original_event")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.text"
    assert content["body"] == "Replying!"
    assert "m.relates_to" in content
    assert content["m.relates_to"]["m.in_reply_to"]["event_id"] == "$original_event"


@pytest.mark.asyncio
async def test_send_file__expect_file_message(room, client):
    from matrix.types import File

    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    file = File(
        path="mxc://example.com/abc123",
        filename="document.pdf",
        mimetype="application/pdf",
    )

    await room.send(file=file)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.file"
    assert content["body"] == "document.pdf"
    assert content["url"] == "mxc://example.com/abc123"


@pytest.mark.asyncio
async def test_send_image__expect_image_message_with_dimensions(room, client):
    from matrix.types import Image

    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    image = Image(
        path="mxc://example.com/xyz789",
        filename="photo.jpg",
        mimetype="image/jpeg",
        width=800,
        height=600,
    )

    await room.send(file=image)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.image"
    assert content["body"] == "photo.jpg"
    assert content["url"] == "mxc://example.com/xyz789"
    assert content["info"]["w"] == 800
    assert content["info"]["h"] == 600


@pytest.mark.asyncio
async def test_send_video__expect_video_message_with_metadata(room, client):
    from matrix.types import Video

    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    video = Video(
        path="mxc://example.com/video123",
        filename="clip.mp4",
        mimetype="video/mp4",
        width=1920,
        height=1080,
        duration=30000,
    )

    await room.send(file=video)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.video"
    assert content["body"] == "clip.mp4"
    assert content["url"] == "mxc://example.com/video123"
    assert content["info"]["w"] == 1920
    assert content["info"]["h"] == 1080
    assert content["info"]["duration"] == 30000


@pytest.mark.asyncio
async def test_send_audio__expect_audio_message_with_duration(room, client):
    from matrix.types import Audio

    client.room_send = AsyncMock()
    mock_response = Mock()
    mock_response.event_id = "$event123"
    client.room_send.return_value = mock_response

    audio = Audio(
        path="mxc://example.com/audio123",
        filename="song.mp3",
        mimetype="audio/mpeg",
        duration=180000,
    )

    await room.send(file=audio)

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.audio"
    assert content["body"] == "song.mp3"
    assert content["url"] == "mxc://example.com/audio123"
    assert content["info"]["duration"] == 180000


@pytest.mark.asyncio
async def test_send_no_content__expect_value_error(room):
    with pytest.raises(ValueError, match="You must provide content or file."):
        await room.send()


@pytest.mark.asyncio
async def test_send_message_with_network_error__expect_matrix_error(room, client):
    client.room_send = AsyncMock()
    client.room_send.side_effect = Exception("Network error")

    with pytest.raises(MatrixError, match="Failed to send message"):
        await room.send("Hello, world!")


@pytest.mark.asyncio
async def test_invite_user__expect_successful_invitation(room, client):
    client.room_invite = AsyncMock()
    client.room_invite.return_value = None

    await room.invite_user("@alice:example.com")

    client.room_invite.assert_awaited_once_with(
        room_id="!room:example.com", user_id="@alice:example.com"
    )


@pytest.mark.asyncio
async def test_invite_user_with_error__expect_matrix_error(room, client):
    client.room_invite = AsyncMock()
    client.room_invite.side_effect = Exception("User not found")

    with pytest.raises(MatrixError, match="Failed to invite user"):
        await room.invite_user("@alice:example.com")


@pytest.mark.asyncio
async def test_ban_user_without_reason__expect_successful_ban(room, client):
    client.room_ban = AsyncMock()
    client.room_ban.return_value = None

    await room.ban_user("@spammer:example.com")

    client.room_ban.assert_awaited_once_with(
        room_id="!room:example.com", user_id="@spammer:example.com", reason=None
    )


@pytest.mark.asyncio
async def test_ban_user_with_reason__expect_successful_ban_with_reason(room, client):
    client.room_ban = AsyncMock()
    client.room_ban.return_value = None

    await room.ban_user("@spammer:example.com", "Spam and harassment")

    client.room_ban.assert_awaited_once_with(
        room_id="!room:example.com",
        user_id="@spammer:example.com",
        reason="Spam and harassment",
    )


@pytest.mark.asyncio
async def test_ban_user_with_error__expect_matrix_error(room, client):
    client.room_ban = AsyncMock()
    client.room_ban.side_effect = Exception("Insufficient permissions")

    with pytest.raises(MatrixError, match="Failed to ban user"):
        await room.ban_user("@spammer:example.com")


@pytest.mark.asyncio
async def test_unban_user__expect_successful_unban(room, client):
    client.room_unban = AsyncMock()
    client.room_unban.return_value = None

    await room.unban_user("@alice:example.com")

    client.room_unban.assert_awaited_once_with(
        room_id="!room:example.com", user_id="@alice:example.com"
    )


@pytest.mark.asyncio
async def test_unban_user_with_error__expect_matrix_error(room, client):
    client.room_unban = AsyncMock()
    client.room_unban.side_effect = Exception("User not banned")

    with pytest.raises(MatrixError, match="Failed to unban user"):
        await room.unban_user("@alice:example.com")


@pytest.mark.asyncio
async def test_kick_user_without_reason__expect_successful_kick(room, client):
    client.room_kick = AsyncMock()
    client.room_kick.return_value = None

    await room.kick_user("@troublemaker:example.com")

    client.room_kick.assert_awaited_once_with(
        room_id="!room:example.com", user_id="@troublemaker:example.com", reason=None
    )


@pytest.mark.asyncio
async def test_kick_user_with_reason__expect_successful_kick_with_reason(room, client):
    client.room_kick = AsyncMock()
    client.room_kick.return_value = None

    await room.kick_user("@troublemaker:example.com", "Violating rules")

    client.room_kick.assert_awaited_once_with(
        room_id="!room:example.com",
        user_id="@troublemaker:example.com",
        reason="Violating rules",
    )


@pytest.mark.asyncio
async def test_kick_user_with_error__expect_matrix_error(room, client):
    client.room_kick = AsyncMock()
    client.room_kick.side_effect = Exception("User not in room")

    with pytest.raises(MatrixError, match="Failed to kick user"):
        await room.kick_user("@troublemaker:example.com")


def test_room_properties__expect_correct_delegation_to_matrix_room(room, matrix_room):
    assert room.room_id == "!room:example.com"
    assert room.name == "Test Room"
    assert room.display_name == "Test Room"
    assert room.topic == "A test room"
    assert room.member_count == 5
    assert room.encrypted is False


def test_room_matrix_room_property__expect_underlying_matrix_room(room, matrix_room):
    assert room.matrix_room is matrix_room


def test_room_client_property__expect_async_client(room, client):
    assert room.client is client
