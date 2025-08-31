import pytest
from matrix.help.help_command import DefaultHelpCommand
from matrix.help.pagination import Paginator, Page
from matrix.command import Command
from matrix.group import Group


class DummyCtx:
    def __init__(self, commands):
        self.bot = type("Bot", (), {"commands": commands})
        self._replies = []

    async def reply(self, msg):
        self._replies.append(msg)

    @property
    def last_reply(self):
        return self._replies[-1] if self._replies else None


@pytest.fixture
def simple_command():
    async def cmd(ctx):
        return "ok"
    return Command(
        cmd,
        name="ping",
        usage="ping",
        description="Check latency"
    )


@pytest.fixture
def simple_group():
    async def group_cb(ctx): return "group"
    async def foo(ctx): return "foo"
    async def bar(ctx): return "bar"

    grp = Group(
        group_cb,
        name="tools",
        usage="tools",
        description="Tool commands"
    )
    grp.register_command(Command(
        foo,
        name="foo",
        usage="foo",
        description="Foo command"
    ))
    grp.register_command(Command(
        bar,
        name="bar",
        usage="bar",
        description="Bar command"
    ))

    return grp


@pytest.fixture
def help_cmd():
    return DefaultHelpCommand()


def test_format_command(help_cmd, simple_command):
    text = help_cmd.format_command(simple_command)
    assert "**ping**" in text
    assert "Usage: `ping`" in text
    assert "Check latency" in text


def test_format_group(help_cmd, simple_group):
    text = help_cmd.format_group(simple_group)
    assert "**tools** [GROUP]" in text
    assert "(2 subcommands)" in text
    assert "Tool commands" in text


def test_format_subcommand(help_cmd, simple_group):
    sub = simple_group.commands["foo"]
    text = help_cmd.format_subcommand(sub)
    assert "**foo**" in text
    assert "Foo command" in text


def test_format_page_info(help_cmd, simple_command):
    paginator = Paginator([simple_command], per_page=1)
    page = paginator.get_page(1)
    assert help_cmd.format_page_info(page) == "**Page 1/1**"


def test_format_help_page_with_commands(help_cmd, simple_command):
    paginator = Paginator([simple_command], per_page=1)
    page = paginator.get_page(1)
    result = help_cmd.format_help_page(page)
    assert "**Commands**" in result
    assert "**ping**" in result
    assert "**Page 1/1**" in result


def test_format_help_page_empty(help_cmd):
    page = Page([], page_number=1, total_pages=1, per_page=5, total_items=0)
    result = help_cmd.format_help_page(page)
    assert result == "No commands available."


def test_format_subcommand_page(help_cmd, simple_group):
    subcommands = list(simple_group.commands.values())
    paginator = Paginator(subcommands, per_page=2)
    page = paginator.get_page(1)
    result = help_cmd.format_subcommand_page(page, simple_group.name)
    assert "**tools Subcommands**" in result
    assert "**foo**" in result or "**bar**" in result


def test_format_group_with_no_subcommands(help_cmd):
    async def cb(ctx): 
        return "ok"
    
    empty_group = Group(
        cb,
        name="empty",
        usage="empty",
        description="Empty group"
    )
    result = help_cmd.format_group(empty_group)

    assert "[GROUP]" in result
    assert "empty" in result
    assert "subcommands)" not in result
