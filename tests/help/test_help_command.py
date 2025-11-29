import pytest

from matrix.help.help_command import HelpCommand
from matrix.help.pagination import Page
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
    group.register_command(
        Command(foo, name="foo", usage="foo", description="Foo command")
    )

    async def bar(ctx): return "bar"
    group.register_command(
        Command(bar, name="bar", usage="bar", description="Bar command")
    )

    return group


@pytest.fixture
def help_cmd():
    return DummyHelpCommand()


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
async def test_show_command_help_invalid_subcommands(help_cmd, simple_group):
    ctx = DummyCtx({"tools": simple_group})
    await help_cmd.execute(ctx, "tools", "invalid")
    assert "Subcommand `invalid` not found." in ctx.last_reply