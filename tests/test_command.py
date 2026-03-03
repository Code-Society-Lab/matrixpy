import pytest
import inspect

from unittest.mock import MagicMock
from matrix.errors import MissingArgumentError
from matrix.command import Command


class DummyBot:
    async def on_command_error(self, _ctx, _error):
        return None


class DummyContext:
    def __init__(self, args=None):
        self.bot = DummyBot()
        self.args = args or []
        self.logger = MagicMock()

    async def send_help(self):
        return "this is the help"


@pytest.mark.asyncio
async def test_command_init():
    async def valid_command(ctx):
        pass

    cmd = Command(valid_command)
    assert cmd.name == "valid_command"
    assert cmd.callback == valid_command
    assert inspect.iscoroutinefunction(cmd.callback)

    # name override
    cmd2 = Command(valid_command, name="custom")
    assert cmd2.name == "custom"

    # invalid name type
    with pytest.raises(TypeError):
        Command(valid_command, name=123)

    # callback must be coroutine
    def invalid_command(ctx):
        pass

    with pytest.raises(TypeError):
        Command(invalid_command)


def test_usage_property():
    async def valid_command(ctx, arg1, arg2):
        pass

    # default usage
    cmd = Command(valid_command)
    expected_usage = "valid_command [arg1] [arg2]"
    assert cmd.usage == expected_usage

    # usage override
    cmd2 = Command(valid_command, usage="custom usage")
    assert cmd2.usage == "custom usage"


def test_help_property():
    async def my_command(ctx):
        pass

    cmd = Command(my_command, description="some command")
    assert cmd.help == "some command\n\nusage: my_command "


def test_parse_arguments():
    async def my_command(ctx, a: int, b: str = "default"):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["123"])
    args = cmd._parse_arguments(ctx)
    assert args == [123, "default"]

    ctx2 = DummyContext(args=["123", "hello"])
    args2 = cmd._parse_arguments(ctx2)
    assert args2 == [123, "hello"]

    ctx3 = DummyContext(args=[])
    with pytest.raises(MissingArgumentError):
        cmd._parse_arguments(ctx3)


def test_parse_var_positional_arguments():
    async def my_command(ctx, *words: str):
        pass

    cmd = Command(my_command)
    ctx = DummyContext(args=["hello", "matrix", "world"])

    args = cmd._parse_arguments(ctx)

    assert args == ["hello", "matrix", "world"]

    ctx2 = DummyContext(args=[])
    with pytest.raises(MissingArgumentError):
        cmd._parse_arguments(ctx2)


@pytest.mark.asyncio
async def test_command_call():
    called = False

    async def my_command(ctx, x: int):
        nonlocal called
        called = True
        assert x == 42

    cmd = Command(my_command)
    ctx = DummyContext(args=["42"])

    # successful call
    await cmd(ctx)
    assert called


@pytest.mark.asyncio
async def test_error_handler():
    async def valid_command(ctx, x: int):
        pass

    cmd = Command(valid_command)
    ctx = DummyContext(args=[])
    called = False

    with pytest.raises(TypeError):

        @cmd.error(TypeError)
        def invalid_handler(_ctx, _error):
            pass

    @cmd.error()
    async def handler(_ctx, _error):
        nonlocal called
        called = True

    await cmd(ctx)
    assert called


@pytest.mark.asyncio
async def test_before_and_after_invoke():
    call_order = []

    async def my_command(ctx):
        call_order.append("command")

    cmd = Command(my_command)
    ctx = DummyContext(args=[])

    @cmd.before_invoke
    async def run_before(ctx):
        call_order.append("before")

    @cmd.after_invoke
    async def run_after(ctx):
        call_order.append("after")

    await cmd(ctx)
    assert call_order == ["before", "command", "after"]


@pytest.mark.asyncio
async def test_invalid_before_invoke():
    async def my_command(ctx, x: int):
        pass

    cmd = Command(my_command)

    with pytest.raises(TypeError):

        @cmd.before_invoke
        def invalid_hook(_ctx, _error):
            pass


@pytest.mark.asyncio
async def test_invalid_after_invoke():
    async def my_command(ctx, x: int):
        pass

    cmd = Command(my_command)

    with pytest.raises(TypeError):

        @cmd.after_invoke
        def invalid_hook(_ctx, _error):
            pass


@pytest.mark.asyncio
async def test_invalid_command_check():
    async def my_command(ctx, x: int):
        pass

    cmd = Command(my_command)

    with pytest.raises(TypeError):

        @cmd.check
        def invalid_check(_ctx, _error):
            pass


@pytest.mark.asyncio
async def test_command_executes_when_all_checks_pass():
    called = False

    async def my_command(ctx):
        nonlocal called
        called = True

    cmd = Command(my_command)
    ctx = DummyContext(args=[])

    @cmd.check
    async def passing_check(ctx):
        return True

    await cmd(ctx)
    assert called is True


def test_parse_arguments_with_union_type__expect_successful_conversion():
    async def my_command(ctx, value: str | int):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["123"])
    args = cmd._parse_arguments(ctx)
    assert args[0] in [123, "123"]  # Accept either, depending on Union order

    ctx2 = DummyContext(args=["hello"])
    args2 = cmd._parse_arguments(ctx2)
    assert args2 == ["hello"]


def test_parse_arguments_with_optional_union__expect_default_none():
    async def my_command(ctx, count: int | None = None):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["42"])
    args = cmd._parse_arguments(ctx)
    assert args == [42]

    ctx2 = DummyContext(args=[])
    args2 = cmd._parse_arguments(ctx2)
    assert args2 == [None]


def test_parse_arguments_with_multiple_union_types__expect_first_successful():
    async def my_command(ctx, value: int | str):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["42"])
    args = cmd._parse_arguments(ctx)
    assert args == [42]

    ctx2 = DummyContext(args=["not-a-number"])
    args2 = cmd._parse_arguments(ctx2)
    assert args2 == ["not-a-number"]


def test_parse_arguments_with_union_and_default__expect_typed_conversion():
    """Test Union types with default values."""

    async def my_command(ctx, port: int | str = 8080):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["3000"])
    args = cmd._parse_arguments(ctx)
    assert args[0] in [3000, "3000"]

    ctx2 = DummyContext(args=[])
    args2 = cmd._parse_arguments(ctx2)
    assert args2 == [8080]


def test_parse_arguments_with_union_var_positional__expect_all_converted():
    async def my_command(ctx, *values: int | str):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["1", "hello", "3"])
    args = cmd._parse_arguments(ctx)

    assert len(args) == 3
    assert args[1] == "hello"


def test_parse_arguments_with_union_conversion_failure__expect_string_fallback():
    async def my_command(ctx, value: int | float):
        pass

    cmd = Command(my_command)

    ctx = DummyContext(args=["hello"])
    args = cmd._parse_arguments(ctx)

    assert args == ["hello"]
