import pytest
import inspect
from unittest.mock import MagicMock

from matrix.errors import MissingArgumentError
from matrix.command import Command  # Adjust to your actual import path


class DummyContext:
    def __init__(self, args=None):
        self.args = args or []
        self.logger = MagicMock()


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
    expected_usage = "valid_command <arg1> <arg2>"
    assert cmd.usage == expected_usage

    # usage override
    cmd2 = Command(valid_command, usage="custom usage")
    assert cmd2.usage == "custom usage"


def test_help_property():
    async def my_command(ctx):
        pass

    cmd = Command(my_command, help="""
        This is
          help text.
    """)
    assert cmd.help == "This is\n  help text."


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

    await cmd(ctx)
    ctx.logger.exception.assert_called_once()

    with pytest.raises(TypeError):
        @cmd.error()
        def invalid_handler(ctx, exc):
            pass

    @cmd.error()
    async def handler(ctx, exc):
        nonlocal called
        called = True

    await cmd(ctx)
    assert called