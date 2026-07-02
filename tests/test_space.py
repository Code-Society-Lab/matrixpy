import pytest
from unittest.mock import AsyncMock, Mock
from nio import MatrixRoom
from matrix.room import Room
from matrix.space import Space


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
