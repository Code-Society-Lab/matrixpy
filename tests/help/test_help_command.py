import pytest

from matrix.help.help_command import HelpCommand
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


class DummyHelpCommand(HelpCommand):
    def format_help_page(
        self,
        page: Page[Command],
        title: str = "Commands"
    ) -> str:
        help_entries = []

        if not page.items:
            return f"No {title.lower()} available."

        for cmd in page.items:
            if isinstance(cmd, Group):
                help_entries.append(self.format_group(cmd))
            else:
                help_entries.append(self.format_command(cmd))

        help_text = "\n\n".join(help_entries)
        page_info = self.format_page_info(page)

        return f"**{title}**\n\n{help_text}\n\n{page_info}"

    def format_subcommand_page(
        self,
        page: Page[Command],
        group_name: str
    ) -> str:
        help_entries = []

        if not page.items:
            return f"No subcommands available for group `{group_name}`."

        for subcmd in page.items:
            help_entries.append(self.format_subcommand(subcmd))

        help_text = "\n\n".join(help_entries)
        page_info = self.format_page_info(page)

        return f"**{group_name} Subcommands**\n\n{help_text}\n\n{page_info}"

    def format_command(self, cmd: Command) -> str:
        return f"CMD:{cmd.name}"

    def format_group(self, group: Group) -> str:
        return f"GRP:{group.name}({len(group.commands)} subcommands)"

    def format_subcommand(self, subcommand: Command) -> str:
        return f"SUB:{subcommand.name}"

    def format_page_info(self, page: Page[Command]) -> str:
        return f"Page {page.page_number}/{page.total_pages}"

    async def on_command_not_found(
        self,
        ctx: DummyCtx,
        command_name: str
    ) -> None:
        await ctx.reply(f"Command `{command_name}` not found.")

    async def on_subcommand_not_found(
        self,
        ctx: DummyCtx,
        group: Group,
        subcommand_name: str
    ) -> None:
        await ctx.reply(f"Subcommand `{subcommand_name}` not found.")

    async def on_page_out_of_range(
        self,
        ctx: DummyCtx,
        page_number: int,
        total_pages: int
    ) -> None:
        await ctx.reply(f"Page {page_number} does not exist.")


@pytest.fixture
def simple_command():
    async def cb(ctx): return "ok"
    return Command(cb, name="ping", usage="ping", description="Check latency")


@pytest.fixture
def simple_group():
    async def cb(ctx): return "ok"
    group = Group(cb, name="tools", usage="tools", description="Tool commands")

    async def foo(ctx): return "foo"
    group.register_command(Command(foo, name="foo", usage="foo", description="Foo command"))

    async def bar(ctx): return "bar"
    group.register_command(Command(bar, name="bar", usage="bar", description="Bar command"))

    return group


@pytest.fixture
def help_cmd():
    return DummyHelpCommand()


def test_format_command(help_cmd, simple_command):
    assert help_cmd.format_command(simple_command) == "CMD:ping"


def test_format_group(help_cmd, simple_group):
    assert help_cmd.format_group(simple_group) == "GRP:tools(2 subcommands)"


def test_format_subcommand(help_cmd, simple_group):
    sub = simple_group.commands["foo"]
    assert help_cmd.format_subcommand(sub) == "SUB:foo"


def test_format_page_info(help_cmd, simple_command):
    paginator = Paginator([simple_command], per_page=1)
    page = paginator.get_page(1)
    assert help_cmd.format_page_info(page) == "Page 1/1"


def test_format_help_page_with_commands(help_cmd, simple_command):
    paginator = Paginator([simple_command], per_page=1)
    page = paginator.get_page(1)
    result = help_cmd.format_help_page(page)
    assert "CMD:ping" in result
    assert "Page 1/1" in result
    assert "**Commands**" in result


def test_format_help_page_empty(help_cmd):
    page = Page([], page_number=1, total_pages=1, per_page=5, total_items=0)
    result = help_cmd.format_help_page(page)
    assert result == "No commands available."


def test_format_subcommand_page(help_cmd, simple_group):
    subs = list(simple_group.commands.values())
    paginator = Paginator(subs, per_page=1)
    page = paginator.get_page(1)
    result = help_cmd.format_subcommand_page(page, simple_group.name)
    assert "**tools Subcommands**" in result
    assert "SUB:foo" in result or "SUB:bar" in result


def test_format_subcommand_page_empty(help_cmd):
    page = Page([], page_number=1, total_pages=1, per_page=5, total_items=0)
    result = help_cmd.format_subcommand_page(page, "tools")
    assert result == "No subcommands available for group `tools`."


def test_get_commands_paginator(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    paginator = help_cmd.get_commands_paginator(ctx)
    page = paginator.get_page(1)
    assert simple_command in page.items


def test_get_subcommands_paginator(help_cmd, simple_group):
    paginator = help_cmd.get_subcommands_paginator(simple_group)
    page = paginator.get_page(1)
    assert "foo" in [cmd.name for cmd in page.items]


def test_find_command(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    assert help_cmd.find_command(ctx, "ping") == simple_command
    assert help_cmd.find_command(ctx, "missing") is None


def test_find_subcommand(help_cmd, simple_group):
    assert help_cmd.find_subcommand(simple_group, "foo").name == "foo"
    assert help_cmd.find_subcommand(simple_group, "missing") is None


@pytest.mark.asyncio
async def test_show_command_help_simple(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    await help_cmd.show_command_help(ctx, simple_command)
    assert "CMD:ping" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_command_help_group(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.show_command_help(ctx, simple_group)
    assert "CMD:tools" in ctx.last_reply


@pytest.mark.asyncio
async def test_execute_no_args_shows_help(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    await help_cmd.execute(ctx)
    assert "**Commands**" in ctx.last_reply


@pytest.mark.asyncio
async def test_execute_command_name(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    await help_cmd.execute(ctx, "ping")
    assert "ping" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_command_help_not_found(help_cmd):
    ctx = DummyCtx({})
    await help_cmd.execute(ctx, "invalid")
    assert "not found" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_subcommand_page(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.show_group_help(ctx, simple_group, page_number=1)
    assert "SUB:foo" in ctx.last_reply or "SUB:bar" in ctx.last_reply

@pytest.mark.asyncio
async def test_show_subcommand_page_not_found(help_cmd):
    ctx = DummyCtx({})
    await help_cmd.execute(ctx, "missing")
    assert "not found" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_help_page(help_cmd, simple_command):
    ctx = DummyCtx({"ping": simple_command})
    await help_cmd.show_help_page(ctx)
    assert "**Commands**" in ctx.last_reply


def test_parse_help_arguments(help_cmd):
    # no args
    assert help_cmd.parse_help_arguments([]) == (None, None, 1)
    # only page
    assert help_cmd.parse_help_arguments(["2"]) == (None, None, 2)
    # command only
    assert help_cmd.parse_help_arguments(["ping"]) == ("ping", None, 1)
    # command + subcommand
    assert help_cmd.parse_help_arguments(["tools", "foo"]) == ("tools", "foo", 1)
    # command + page
    assert help_cmd.parse_help_arguments(["tools", "2"]) == ("tools", None, 2)
    # command + subcommand + page
    assert help_cmd.parse_help_arguments(["tools", "foo", "2"]) == ("tools", "foo", 2)


@pytest.mark.asyncio
async def test_execute_group_subcommand(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.execute(ctx, "tools", "foo")
    assert "foo" in ctx.last_reply


@pytest.mark.asyncio
async def test_execute_group_page(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.execute(ctx, "tools", "1")
    assert "Subcommands" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_help_page_group(help_cmd, simple_group):
    ctx = DummyCtx({"simple_group": simple_group})

    await help_cmd.show_help_page(ctx)
    assert "**Commands**" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_command_help_group_no_subcommands(help_cmd):
    async def empty(ctx): return "ok"
    empty_group = Group(
        empty,
        name="misc",
        usage="misc",
        description="Misc group"
    )
    ctx = DummyCtx({"misc": empty_group})

    await help_cmd.show_command_help(ctx, empty_group)
    assert "CMD:misc" in ctx.last_reply


@pytest.mark.asyncio
async def test_show_command_help_invalid_subcommands(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.execute(ctx, "tools", "invalid")
    assert "Subcommand `invalid` not found." in ctx.last_reply
