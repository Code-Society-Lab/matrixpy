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

    with pytest.raises(MissingArgumentError):
        await cmd(ctx)
    ctx.logger.exception.assert_called_once()

    with pytest.raises(TypeError):
        @cmd.error(TypeError)
        def invalid_handler(_ctx, _error):
            pass

    @cmd.error()
    async def handler(_ctx, _error):
        nonlocal called
        called = True

    with pytest.raises(MissingArgumentError):
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


@pytest.mark.asyncio
async def test_command_does_not_execute_when_a_check_fails():
    called = False

    async def my_command(ctx):
        nonlocal called
        called = True

    cmd = Command(my_command)
    ctx = DummyContext(args=[])

    @cmd.check
    async def always_fails(ctx):
        return False

    with pytest.raises(Exception):
        await cmd(ctx)
    assert called is False
