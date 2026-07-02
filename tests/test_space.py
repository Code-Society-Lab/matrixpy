import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from nio import MatrixRoom, Event
from matrix.room import Room
from matrix.space import Space
from matrix.message import Message


@pytest.fixture
def client():
    return AsyncMock()


@pytest.fixture
def matrix_space():
    space = MatrixRoom(room_id="!space:example.com", own_user_id="@bot:example.com")
    space.name = "Test Space"
    space.room_type = "m.space"
    return space


@pytest.fixture
def space(matrix_space, client):
    return Space(matrix_space, client)


@pytest.fixture
def mock_send_response(client):
    """Set up client to return a mock event after room_send and fetch_event."""
    send_response = Mock()
    send_response.event_id = "$event123"
    client.room_send = AsyncMock(return_value=send_response)

    mock_event = MagicMock(spec=Event)
    mock_event.event_id = "$event123"

    get_event_response = Mock()
    get_event_response.event = mock_event
    client.room_get_event = AsyncMock(return_value=get_event_response)

    return send_response


def test_get_children__with_room_child__expect_room_instance(
    space, matrix_space, client
):
    child = MatrixRoom(room_id="!child:example.com", own_user_id="@bot:example.com")
    child.name = "Child Room"
    matrix_space.children = {"!child:example.com"}
    client.rooms = {"!child:example.com": child}

    result = space.get_children()

    assert len(result) == 1
    assert type(result[0]) is Room
    assert result[0].room_id == "!child:example.com"


def test_get_children__with_space_child__expect_space_instance(
    space, matrix_space, client
):
    child = MatrixRoom(room_id="!subspace:example.com", own_user_id="@bot:example.com")
    child.name = "Sub Space"
    child.room_type = "m.space"
    matrix_space.children = {"!subspace:example.com"}
    client.rooms = {"!subspace:example.com": child}

    result = space.get_children()

    assert len(result) == 1
    assert isinstance(result[0], Space)
    assert result[0].room_id == "!subspace:example.com"


def test_get_children__with_unjoined_child__expect_child_skipped(
    space, matrix_space, client
):
    matrix_space.children = {"!unknown:example.com"}
    client.rooms = {}

    result = space.get_children()

    assert result == []


def test_get_children__with_no_children__expect_empty_list(space, matrix_space, client):
    matrix_space.children = set()
    client.rooms = {}

    result = space.get_children()

    assert result == []


def test_get_children__with_mixed_children__expect_correct_types(
    space, matrix_space, client
):
    room_child = MatrixRoom(room_id="!room:example.com", own_user_id="@bot:example.com")
    space_child = MatrixRoom(room_id="!sub:example.com", own_user_id="@bot:example.com")
    space_child.room_type = "m.space"
    matrix_space.children = {"!room:example.com", "!sub:example.com"}
    client.rooms = {
        "!room:example.com": room_child,
        "!sub:example.com": space_child,
    }

    result = space.get_children()

    assert len(result) == 2
    types = {r.room_id: type(r) for r in result}
    assert types["!room:example.com"] is Room
    assert types["!sub:example.com"] is Space


def test_get_children__with_negative_depth__expect_value_error(space, matrix_space):
    with pytest.raises(ValueError, match="depth must be a non-negative integer"):
        space.get_children(depth=-1)


def test_get_children__with_depth_zero__expect_empty_list(space, matrix_space, client):
    child = MatrixRoom(room_id="!child:example.com", own_user_id="@bot:example.com")
    matrix_space.children = {"!child:example.com"}
    client.rooms = {"!child:example.com": child}

    result = space.get_children(depth=0)

    assert result == []


def test_get_children__with_depth_one__expect_no_recursion(space, matrix_space, client):
    subspace = MatrixRoom(
        room_id="!subspace:example.com", own_user_id="@bot:example.com"
    )
    subspace.room_type = "m.space"
    nested = MatrixRoom(room_id="!nested:example.com", own_user_id="@bot:example.com")
    subspace.children = {"!nested:example.com"}
    matrix_space.children = {"!subspace:example.com"}
    client.rooms = {
        "!subspace:example.com": subspace,
        "!nested:example.com": nested,
    }

    result = space.get_children(depth=1)

    assert len(result) == 1
    assert result[0].room_id == "!subspace:example.com"


def test_get_children__with_depth_two__expect_recursive_children(
    space, matrix_space, client
):
    subspace = MatrixRoom(
        room_id="!subspace:example.com", own_user_id="@bot:example.com"
    )
    subspace.room_type = "m.space"
    nested = MatrixRoom(room_id="!nested:example.com", own_user_id="@bot:example.com")
    subspace.children = {"!nested:example.com"}
    matrix_space.children = {"!subspace:example.com"}
    client.rooms = {
        "!subspace:example.com": subspace,
        "!nested:example.com": nested,
    }

    result = space.get_children(depth=2)

    assert len(result) == 2
    ids = [r.room_id for r in result]
    assert "!subspace:example.com" in ids
    assert "!nested:example.com" in ids

@pytest.mark.asyncio
async def test_broadcast__expect_message_sent_to_all_children(
    space, matrix_space, client, mock_send_response
):
    child1 = MatrixRoom(room_id="!child1:example.com", own_user_id="@bot:example.com")
    child1.name = "Child 1"
    child2 = MatrixRoom(room_id="!child2:example.com", own_user_id="@bot:example.com")
    child2.name = "Child 2"
    matrix_space.children = {"!child1:example.com", "!child2:example.com"}
    client.rooms = {
        "!child1:example.com": child1,
        "!child2:example.com": child2,
    }

    results = await space.broadcast("Hello!")

    assert len(results) == 2
    assert all(isinstance(msg, Message) for msg in results)
    assert client.room_send.await_count == 2


@pytest.mark.asyncio
async def test_broadcast__with_no_children__expect_empty_list(
    space, matrix_space, client
):
    matrix_space.children = set()
    client.rooms = {}

    results = await space.broadcast("Hello!")

    assert results == []
    client.room_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast__with_unjoined_children__expect_empty_list(
    space, matrix_space, client
):
    matrix_space.children = {"!unknown:example.com"}
    client.rooms = {}

    results = await space.broadcast("Hello!")

    assert results == []
    client.room_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_raw__expect_unformatted_messages(
    space, matrix_space, client, mock_send_response
):
    child = MatrixRoom(room_id="!child:example.com", own_user_id="@bot:example.com")
    child.name = "Child"
    matrix_space.children = {"!child:example.com"}
    client.rooms = {"!child:example.com": child}

    await space.broadcast("Hello world!", raw=True)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.text"
    assert content["body"] == "Hello world!"
    assert "formatted_body" not in content


@pytest.mark.asyncio
async def test_broadcast_notice__expect_notice_message_type(
    space, matrix_space, client, mock_send_response
):
    child = MatrixRoom(room_id="!child:example.com", own_user_id="@bot:example.com")
    child.name = "Child"
    matrix_space.children = {"!child:example.com"}
    client.rooms = {"!child:example.com": child}

    await space.broadcast("Special Event started!", notice=True)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.notice"
    assert content["body"] == "Special Event started!"


@pytest.mark.asyncio
async def test_broadcast_file__expect_file_message(
    space, matrix_space, client, mock_send_response
):
    from matrix.types import File

    child = MatrixRoom(room_id="!child:example.com", own_user_id="@bot:example.com")
    child.name = "Child"
    matrix_space.children = {"!child:example.com"}
    client.rooms = {"!child:example.com": child}

    file = File(
        path="mxc://example.com/abc123",
        filename="document.pdf",
        mimetype="application/pdf",
    )

    await space.broadcast(file=file)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.file"
    assert content["body"] == "document.pdf"
    assert content["url"] == "mxc://example.com/abc123"


@pytest.mark.asyncio
async def test_broadcast__with_mixed_children__expect_message_to_all(
    space, matrix_space, client, mock_send_response
):
    room_child = MatrixRoom(room_id="!room:example.com", own_user_id="@bot:example.com")
    room_child.name = "Room Child"
    space_child = MatrixRoom(room_id="!sub:example.com", own_user_id="@bot:example.com")
    space_child.name = "Sub Space"
    space_child.room_type = "m.space"
    matrix_space.children = {"!room:example.com", "!sub:example.com"}
    client.rooms = {
        "!room:example.com": room_child,
        "!sub:example.com": space_child,
    }

    results = await space.broadcast("Hello!")

    assert len(results) == 2
    assert client.room_send.await_count == 2
    sent_room_ids = {
        call.kwargs["room_id"] for call in client.room_send.await_args_list
    }
    assert sent_room_ids == {"!room:example.com", "!sub:example.com"}
