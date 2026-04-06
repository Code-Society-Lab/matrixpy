import pytest

from unittest.mock import MagicMock
from typing import Optional

from matrix.extension import Extension
from matrix.room import Room


class MockBot:
    prefix: str = "!"

    def __init__(self, room: Optional[Room] = None) -> None:
        self.get_room = MagicMock(return_value=room or MagicMock(spec=Room))


@pytest.fixture
def extension() -> Extension:
    return Extension(name="test_ext", prefix="!")


@pytest.fixture
def bot() -> MockBot:
    return MockBot()


# INIT


def test_init_with_name_and_prefix__expect_attributes_set():
    ext = Extension(name="math", prefix="!")

    assert ext.name == "math"
    assert ext.prefix == "!"


def test_init_with_name_only__expect_prefix_is_none():
    ext = Extension(name="math")

    assert ext.prefix is None


def test_init__expect_bot_is_none(extension: Extension):
    assert extension.bot is None


def test_init__expect_on_load_is_none(extension: Extension):
    assert extension._on_load is None


def test_init__expect_on_unload_is_none(extension: Extension):
    assert extension._on_unload is None


def test_init__expect_empty_commands(extension: Extension):
    assert extension.commands == {}


def test_init__expect_empty_event_handlers(extension: Extension):
    assert extension._event_handlers == {}


def test_init__expect_empty_error_handlers(extension: Extension):
    assert extension._error_handlers == {}


def test_init__expect_empty_checks(extension: Extension):
    assert extension._checks == []


# ON LOAD


def test_on_load_with_sync_function__expect_handler_registered(extension: Extension):
    @extension.on_load
    def setup():
        pass

    assert extension._on_load is setup


def test_on_load_with_coroutine__expect_type_error(extension: Extension):
    with pytest.raises(TypeError):

        @extension.on_load
        async def setup():
            pass


def test_on_load_returns_the_original_function__expect_same_reference(
    extension: Extension,
):
    def setup():
        pass

    result = extension.on_load(setup)

    assert result is setup


def test_on_load_overwrites_previous_handler__expect_latest_handler(
    extension: Extension,
):
    @extension.on_load
    def first():
        pass

    @extension.on_load
    def second():
        pass

    assert extension._on_load is second


# LOAD


def test_load__expect_bot_set(extension: Extension, bot: MockBot):
    extension.load(bot)

    assert extension.bot is bot


def test_load_with_registered_handler__expect_handler_called(
    extension: Extension, bot: MockBot
):
    called = []

    @extension.on_load
    def setup():
        called.append(True)

    extension.load(bot)

    assert called == [True]


def test_load_with_no_handler__expect_no_error(extension: Extension, bot: MockBot):
    extension.load(bot)


# ON UNLOAD


def test_on_unload_with_sync_function__expect_handler_registered(extension: Extension):
    @extension.on_unload
    def teardown():
        pass

    assert extension._on_unload is teardown


def test_on_unload_with_coroutine__expect_type_error(extension: Extension):
    with pytest.raises(TypeError):

        @extension.on_unload
        async def teardown():
            pass


def test_on_unload_returns_the_original_function__expect_same_reference(
    extension: Extension,
):
    def teardown():
        pass

    result = extension.on_unload(teardown)

    assert result is teardown


def test_on_unload_overwrites_previous_handler__expect_latest_handler(
    extension: Extension,
):
    @extension.on_unload
    def first():
        pass

    @extension.on_unload
    def second():
        pass

    assert extension._on_unload is second


# UNLOAD


def test_unload__expect_bot_cleared(extension: Extension, bot: MockBot):
    extension.load(bot)
    extension.unload()

    assert extension.bot is None


def test_unload_with_registered_handler__expect_handler_called(
    extension: Extension, bot: MockBot
):
    called = []

    @extension.on_unload
    def teardown():
        called.append(True)

    extension.load(bot)
    extension.unload()

    assert called == [True]


def test_unload_with_no_handler__expect_no_error(extension: Extension, bot: MockBot):
    extension.load(bot)
    extension.unload()


# GET ROOM


def test_get_room_before_load__expect_runtime_error(extension: Extension):
    with pytest.raises(RuntimeError, match="Extension is not loaded"):
        extension.get_room("!room:example.com")


def test_get_room_after_load__expect_delegates_to_bot(
    extension: Extension, bot: MockBot
):
    room_id = "!room:example.com"
    expected_room = MagicMock(spec=Room)
    bot.get_room.return_value = expected_room

    extension.load(bot)
    result = extension.get_room(room_id)

    bot.get_room.assert_called_once_with(room_id)
    assert result is expected_room


def test_get_room_after_unload__expect_runtime_error(
    extension: Extension, bot: MockBot
):
    extension.load(bot)
    extension.unload()

    with pytest.raises(RuntimeError, match="Extension is not loaded"):
        extension.get_room("!room:example.com")
