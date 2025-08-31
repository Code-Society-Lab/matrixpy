import pytest
from unittest.mock import AsyncMock, MagicMock
from matrix.help import Paginator, Page, HelpCommand  # adjust module path
from matrix.command import Command
from matrix.group import Group
from matrix.context import Context


class DummyCommand(Command):
    def __init__(self, name, description="desc", usage="usage"):
        async def dummy_func(ctx):
            pass

        super().__init__(func=dummy_func, name=name, description=description)
        self.usage = usage


class DummyGroup(Group):
    def __init__(self, name, description="group desc", commands=None):
        async def dummy_group_func(ctx):
            pass

        super().__init__(callback=dummy_group_func, name=name, description=description)
        self.usage = f"{name} <subcommand>"
        self.commands = commands or {}


class DummyContext(Context):
    def __init__(self, commands):
        self.bot = MagicMock()
        self.bot.commands = {cmd.name: cmd for cmd in commands}
        self.reply = AsyncMock()


@pytest.fixture
def commands():
    return [
        DummyCommand("alpha"), DummyCommand("beta"),
        DummyCommand("gamma"), DummyCommand("delta"),
        DummyCommand("epsilon")
    ]


@pytest.fixture
def mixed_commands():
    """Commands and groups mixed together"""
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something"),
        "list": DummyCommand("list", "List items")
    }

    group = DummyGroup("manage", "Management commands", subcommands)

    return [
        DummyCommand("alpha"),
        DummyCommand("beta"), 
        group,
        DummyCommand("gamma")
    ]


def test_format_help_page_no_commands():
    hc = HelpCommand()
    empty_page = Page(
        items=[],
        page_number=1,
        total_pages=1,
        per_page=5,
        total_items=0
    )
    result = hc.format_help_page(empty_page)
    assert result == "No commands available."


def test_paginator_basic(commands):
    p = Paginator(commands, per_page=2)
    assert p.total_items == 5
    assert p.total_pages == 3  # ceil(5/2)=3

    page1 = p.get_page(1)
    assert len(page1.items) == 2
    assert page1.has_previous is False and page1.has_next is True

    page3 = p.get_page(3)
    assert len(page3.items) == 1
    assert page3.has_previous is True and page3.has_next is False


def test_paginator_edge_cases():
    # Empty list
    p_empty = Paginator([], per_page=5)
    assert p_empty.total_pages == 1
    assert p_empty.total_items == 0

    page = p_empty.get_page(1)
    assert len(page.items) == 0

    p_single = Paginator([DummyCommand("single")], per_page=5)
    assert p_single.total_pages == 1

    page_negative = p_single.get_page(-5)
    assert page_negative.page_number == 1

    page_too_high = p_single.get_page(999)
    assert page_too_high.page_number == 1


def test_get_pages(commands):
    pages = Paginator(commands, per_page=2).get_pages()
    assert len(pages) == 3
    assert [p.page_number for p in pages] == [1, 2, 3]


def test_page_nav_properties():
    pg1 = Page(items=[], page_number=1, total_pages=3, per_page=5, total_items=10)
    assert not pg1.has_previous and pg1.has_next
    assert pg1.previous_page is None and pg1.next_page == 2

    pg2 = Page(items=[], page_number=2, total_pages=3, per_page=5, total_items=10)
    assert pg2.has_previous and pg2.has_next
    assert pg2.previous_page == 1 and pg2.next_page == 3

    pg3 = Page(items=[], page_number=3, total_pages=3, per_page=5, total_items=10)
    assert pg3.has_previous and not pg3.has_next
    assert pg3.previous_page == 2 and pg3.next_page is None


def test_format_group():
    hc = HelpCommand()
    subcommands = {
        "add": DummyCommand("add"),
        "remove": DummyCommand("remove")
    }
    group = DummyGroup("manage", "Management commands", subcommands)

    formatted = hc.format_group(group)
    assert "**manage** [GROUP]" in formatted
    assert "Management commands" in formatted
    assert "`manage <subcommand>`" in formatted


def test_format_group_no_subcommands():
    hc = HelpCommand()
    group = DummyGroup("empty", "Empty group", {})

    formatted = hc.format_group(group)
    assert "**empty** [GROUP]" in formatted
    assert "Empty group" in formatted


def test_format_subcommand():
    hc = HelpCommand()
    subcmd = DummyCommand("add", "Add something", "manage add <item>")

    formatted = hc.format_subcommand(subcmd)
    assert "**add**" in formatted
    assert "`manage add <item>`" in formatted
    assert "Add something" in formatted


def test_format_subcommand_page():
    hc = HelpCommand()
    subcommands = [
        DummyCommand("add", "Add something"),
        DummyCommand("remove", "Remove something")
    ]

    page = Page(
        items=subcommands,
        page_number=1,
        total_pages=1,
        per_page=5,
        total_items=2
    )

    formatted = hc.format_subcommand_page(page, "manage")
    assert "**manage Subcommands**" in formatted
    assert "**add**" in formatted
    assert "**remove**" in formatted
    assert "Page 1/1" in formatted


def test_format_subcommand_page_empty():
    hc = HelpCommand()
    empty_page = Page(
        items=[],
        page_number=1,
        total_pages=1,
        per_page=5,
        total_items=0
    )

    result = hc.format_subcommand_page(empty_page, "manage")
    assert result == "No subcommands available for group `manage`."


def test_get_commands_paginator(mixed_commands):
    ctx = DummyContext(mixed_commands)
    hc = HelpCommand(per_page=2)

    paginator = hc.get_commands_paginator(ctx)
    assert paginator.total_items == 4
    assert paginator.per_page == 2

    first_page = paginator.get_page(1)
    command_names = [cmd.name for cmd in first_page.items]
    assert command_names == ["alpha", "beta"]


def test_get_subcommands_paginator():
    hc = HelpCommand(per_page=2)
    subcommands = {
        "zebra": DummyCommand("zebra"),
        "alpha": DummyCommand("alpha"),
        "beta": DummyCommand("beta")
    }
    group = DummyGroup("manage", commands=subcommands)

    paginator = hc.get_subcommands_paginator(group)
    assert paginator.total_items == 3

    first_page = paginator.get_page(1)
    subcommand_names = [cmd.name for cmd in first_page.items]
    assert subcommand_names == ["alpha", "beta"]


def test_find_command(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand()

    found = hc.find_command(ctx, "alpha")
    assert found is not None
    assert found.name == "alpha"

    not_found = hc.find_command(ctx, "nonexistent")
    assert not_found is None


def test_find_subcommand():
    hc = HelpCommand()
    subcommands = {
        "add": DummyCommand("add"),
        "remove": DummyCommand("remove")
    }
    group = DummyGroup("manage", commands=subcommands)

    found = hc.find_subcommand(group, "add")
    assert found is not None
    assert found.name == "add"
    
    not_found = hc.find_subcommand(group, "nonexistent")
    assert not_found is None


def test_parse_help_arguments():
    hc = HelpCommand()

    # No arguments
    cmd, sub, page = hc.parse_help_arguments([])
    assert cmd is None and sub is None and page == 1

    # Just page number
    cmd, sub, page = hc.parse_help_arguments(["3"])
    assert cmd is None and sub is None and page == 3

    # Command name only
    cmd, sub, page = hc.parse_help_arguments(["ping"])
    assert cmd == "ping" and sub is None and page == 1

    # Command name and page number
    cmd, sub, page = hc.parse_help_arguments(["ping", "2"])
    assert cmd == "ping" and sub is None and page == 2

    # Command name and subcommand
    cmd, sub, page = hc.parse_help_arguments(["manage", "add"])
    assert cmd == "manage" and sub == "add" and page == 1

    # Command name, subcommand, and page number
    cmd, sub, page = hc.parse_help_arguments(["manage", "add", "2"])
    assert cmd == "manage" and sub == "add" and page == 2


@pytest.mark.asyncio
async def test_show_command_help_regular_command(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand()

    await hc.show_command_help(ctx, "alpha")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**alpha**" in sent


@pytest.mark.asyncio
async def test_show_command_help_not_found(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand()

    await hc.show_command_help(ctx, "nonexistent")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "Command `nonexistent` not found." in sent


@pytest.mark.asyncio
async def test_show_command_help_group_with_subcommands():
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something"),
        "list": DummyCommand("list", "List items")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand(per_page=2)

    await hc.show_command_help(ctx, "manage")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**manage** [GROUP]" in sent
    assert "**manage Subcommands**" in sent
    assert "Page 1/" in sent


@pytest.mark.asyncio
async def test_show_command_help_group_no_subcommands():
    group = DummyGroup("empty", "Empty group", {})
    ctx = DummyContext([group])
    hc = HelpCommand()

    await hc.show_command_help(ctx, "empty")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**empty** [GROUP]" in sent
    assert "No subcommands available." in sent


@pytest.mark.asyncio
async def test_show_command_help_specific_subcommand():
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand()

    await hc.show_command_help(ctx, "manage", "add")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**add**" in sent
    assert "Add something" in sent


@pytest.mark.asyncio
async def test_show_command_help_subcommand_not_group():
    regular_cmd = DummyCommand("ping", "Ping command")
    ctx = DummyContext([regular_cmd])
    hc = HelpCommand()

    await hc.show_command_help(ctx, "ping", "subcommand")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "Command `ping` is not a group." in sent


@pytest.mark.asyncio
async def test_show_help_page(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    await hc.show_help_page(ctx, page_number=2)
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**Commands**" in sent
    assert "Page 2/" in sent


@pytest.mark.asyncio
async def test_show_subcommand_page():
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something"),
        "list": DummyCommand("list", "List items"),
        "update": DummyCommand("update", "Update something")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand(per_page=2)

    await hc.show_subcommand_page(ctx, "manage", page_number=2)
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**manage Subcommands**" in sent
    assert "Page 2/" in sent


@pytest.mark.asyncio
async def test_show_subcommand_page_group_not_found():
    ctx = DummyContext([])
    hc = HelpCommand()

    await hc.show_subcommand_page(ctx, "nonexistent")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "Group `nonexistent` not found." in sent


@pytest.mark.asyncio
async def test_show_subcommand_page_not_group():
    regular_cmd = DummyCommand("ping", "Ping command")
    ctx = DummyContext([regular_cmd])
    hc = HelpCommand()

    await hc.show_subcommand_page(ctx, "ping")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "Command `ping` is not a group." in sent


@pytest.mark.asyncio
async def test_execute_no_args(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    await hc.execute(ctx)
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**Commands**" in sent
    assert "Page 1/" in sent


@pytest.mark.asyncio
async def test_execute_page_number_only(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    await hc.execute(ctx, "2")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "Page 2/" in sent


@pytest.mark.asyncio
async def test_execute_command_name_only(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand()

    await hc.execute(ctx, "alpha")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**alpha**" in sent


@pytest.mark.asyncio
async def test_execute_group_command():
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand()

    await hc.execute(ctx, "manage")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**manage Subcommands**" in sent


@pytest.mark.asyncio
async def test_execute_group_with_page_number():
    subcommands = {
        "add": DummyCommand("add"),
        "remove": DummyCommand("remove"),
        "list": DummyCommand("list"),
        "update": DummyCommand("update")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand(per_page=2)

    await hc.execute(ctx, "manage", "2")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**manage Subcommands**" in sent
    assert "Page 2/" in sent


@pytest.mark.asyncio
async def test_execute_specific_subcommand():
    subcommands = {
        "add": DummyCommand("add", "Add something"),
        "remove": DummyCommand("remove", "Remove something")
    }
    group = DummyGroup("manage", "Management commands", subcommands)
    ctx = DummyContext([group])
    hc = HelpCommand()

    await hc.execute(ctx, "manage", "add")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]

    assert "**add**" in sent
    assert "Add something" in sent


@pytest.mark.asyncio
async def test_execute_string_args_conversion():
    """Test that string arguments are properly converted for parsing"""
    commands = [DummyCommand(f"cmd{i}") for i in range(6)]  # Create enough commands for page 2
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    await hc.execute(ctx, "2")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]
    assert "Page 2/" in sent


def test_help_formatting_mixed_commands(mixed_commands):
    ctx = DummyContext(mixed_commands)
    hc = HelpCommand(per_page=2)

    page = hc.get_commands_paginator(ctx).get_page(1)
    help_text = hc.format_help_page(page)

    assert "**Commands**" in help_text
    assert "Page 1/" in help_text

    assert "**" in help_text  # Bold formatting should be present


@pytest.mark.asyncio
async def test_help_command_integration_with_groups():
    """Integration test for complete help command workflow with groups"""
    subcommands = {
        "create": DummyCommand("create", "Create new item"),
        "delete": DummyCommand("delete", "Delete item"),
        "modify": DummyCommand("modify", "Modify item")
    }
    group = DummyGroup("item", "Item management", subcommands)
    regular_cmd = DummyCommand("ping", "Ping the server")

    ctx = DummyContext([group, regular_cmd])
    hc = HelpCommand(per_page=2)

    # Test main help page
    await hc.execute(ctx)
    assert ctx.reply.call_count == 1

    ctx.reply.reset_mock()

    await hc.execute(ctx, "item")
    sent = ctx.reply.call_args[0][0]
    assert "**item Subcommands**" in sent

    ctx.reply.reset_mock()

    await hc.execute(ctx, "item", "create")
    sent = ctx.reply.call_args[0][0]
    assert "**create**" in sent
    assert "Create new item" in sent


def test_paginator_ceil_division():
    """
    Test that paginator correctly calculates total pages usingceiling division
    """
    items = [DummyCommand(f"cmd{i}") for i in range(7)]
    p = Paginator(items, per_page=3)
    assert p.total_pages == 3

    items = [DummyCommand(f"cmd{i}") for i in range(6)]
    p = Paginator(items, per_page=3)
    assert p.total_pages == 2


@pytest.mark.asyncio
async def test_help_sorting_is_case_insensitive():
    """Test that command sorting is case-insensitive"""
    commands = [
        DummyCommand("Zebra"),
        DummyCommand("alpha"),
        DummyCommand("Beta")
    ]
    ctx = DummyContext(commands)
    hc = HelpCommand()

    paginator = hc.get_commands_paginator(ctx)
    page = paginator.get_page(1)

    command_names = [cmd.name for cmd in page.items]
    assert command_names == ["alpha", "Beta", "Zebra"]


def test_format_group_with_no_commands_attribute():
    """Test formatting a group that doesn't have a commands attribute"""
    hc = HelpCommand()
    
    group = DummyGroup("test", "Test group")
    if hasattr(group, 'commands'):
        delattr(group, 'commands')

    formatted = hc.format_group(group)
    assert "**test** [GROUP]" in formatted
    assert "Test group" in formatted


def test_get_subcommands_paginator_no_commands_attribute():
    """Test subcommand paginator with group that has no commands attribute"""
    hc = HelpCommand()
    group = DummyGroup("test", "Test group")
    if hasattr(group, 'commands'):
        delattr(group, 'commands')
    
    paginator = hc.get_subcommands_paginator(group)
    assert paginator.total_items == 0
    assert paginator.total_pages == 1