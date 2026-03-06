import pytest

from matrix.extension import Extension


@pytest.fixture
def extension() -> Extension:
    return Extension(name="test_ext", prefix="!")


def test_init_with_name_and_prefix__expect_attributes_set():
    ext = Extension(name="math", prefix="!")

    assert ext.name == "math"
    assert ext.prefix == "!"


def test_init_with_name_only__expect_prefix_is_none():
    ext = Extension(name="math")

    assert ext.prefix is None


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


def test_load_with_registered_handler__expect_handler_called(extension: Extension):
    called = []

    @extension.on_load
    def setup():
        called.append(True)

    extension.load()

    assert called == [True]


def test_load_with_no_handler__expect_no_error(extension: Extension):
    extension.load()


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


def test_unload_with_registered_handler__expect_handler_called(extension: Extension):
    called = []

    @extension.on_unload
    def teardown():
        called.append(True)

    extension.unload()

    assert called == [True]


def test_unload_with_no_handler__expect_no_error(extension: Extension):
    extension.unload()
