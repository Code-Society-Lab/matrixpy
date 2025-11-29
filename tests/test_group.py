import pytest

from unittest.mock import MagicMock
from matrix.command import Command
from matrix.group import Group
from matrix.errors import AlreadyRegisteredError, CommandNotFoundError


class DummyCtx:
    def __init__(self, args=None):
        self.args = args or []
        self.subcommand = None
        self.called = []

    async def __call__(self):
        self.called.append("called")

    async def reply(self, msg):
        self.called.append(msg)


@pytest.fixture
def command_group():
    async def cb(ctx): return "ok"
    group = Group(cb, name="tools", usage="tools", description="Tool commands")

    async def foo(ctx): return "foo"
    group.register_command(
        Command(foo, name="foo", usage="foo", description="Foo command")
    )

    return group


def test_register_command__expect_command(
    command_group: Group
):
    async def bar(ctx): return "bar"
    cmd = Command(bar, name="bar", usage="bar", description="Bar command")
    assert command_group.register_command(cmd) == cmd


def test_register_command_with_already_register__expect_already_registered_error(
    command_group: Group
):
    async def foo(ctx): return "foo"
    cmd = Command(foo, name="foo", usage="foo", description="Foo command")

    with pytest.raises(AlreadyRegisteredError):
        command_group.register_command(cmd)


def test_get_command_with_valid_command__expect_command(
    command_group: Group
):
    cmd = command_group.get_command("foo")
    assert cmd.name == "foo"


def test_get_command_with_invalid_command__expect_command_not_found(
    command_group: Group
):
    with pytest.raises(CommandNotFoundError):
        command_group.get_command("invalid")


def test_command_with_decorator__registers_command(
    command_group: Group,
    monkeypatch: pytest.MonkeyPatch
):
    calls = []
    original = command_group.register_command

    def wrapped(cmd):
        calls.append(cmd)
        return original(cmd)

    monkeypatch.setattr(
        command_group,
        "register_command",
        wrapped
    )

    @command_group.command(name="baz")
    async def baz(ctx):
        return "baz"

    assert command_group.get_command("baz") is calls[0]


@pytest.mark.asyncio
async def test_invoke_without_subcommand__invokes_group_callback():
    called = []

    async def group_callback(ctx):
        called.append("main")

    group = Group(group_callback, name="tools", prefix="!")
    ctx = DummyCtx(args=[""])

    await group.invoke(ctx)

    assert called == ["main"]
    assert ctx.subcommand is None
    assert ctx.args == []


@pytest.mark.asyncio
async def test_invoke_with_subcommand__invokes_subcommand():
    called = []

    async def group_callback(ctx):
        called.append("main")

    async def subcommand(ctx):
        called.append("sub")

    group = Group(group_callback, name="tools", prefix="!")
    group.register_command(Command(subcommand, name="foo"))

    ctx = DummyCtx(args=["foo"])

    await group.invoke(ctx)

    # Check that the subcommand was invoked
    assert called == ["sub"]
    assert ctx.subcommand.name == "foo"
    assert ctx.args == []
