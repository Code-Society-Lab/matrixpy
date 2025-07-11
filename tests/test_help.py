# tests/test_help_and_paginator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from matrix.help import Paginator, Page, HelpCommand  # adjust module path
from matrix.command import Command
from matrix.context import Context


class DummyCommand(Command):
    def __init__(self, name, description="desc", usage="usage"):
        async def dummy_func(ctx):
            pass

        super().__init__(func=dummy_func, name=name, description=description)
        self.usage = usage


class DummyContext(Context):
    def __init__(self, commands):
        self.bot = MagicMock()
        self.bot.commands = {cmd.name: cmd for cmd in commands}
        self.reply = AsyncMock()


@pytest.fixture
def commands():
    return [
        DummyCommand("one"), DummyCommand("two"),
        DummyCommand("three"), DummyCommand("four"),
        DummyCommand("five")
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
    assert [c.name for c in page1.items] == ["one", "two"]
    assert page1.has_previous is False and page1.has_next is True

    page3 = p.get_page(3)
    assert [c.name for c in page3.items] == ["five"]
    assert page3.has_previous is True and page3.has_next is False


def test_get_pages(commands):
    pages = Paginator(commands, per_page=2).get_pages()
    assert len(pages) == 3
    assert [p.page_number for p in pages] == [1, 2, 3]


def test_page_nav_properties():
    pg = Page(items=[], page_number=1, total_pages=1, per_page=5, total_items=0)
    assert not pg.has_previous and not pg.has_next
    assert pg.previous_page is None and pg.next_page is None


@pytest.mark.asyncio
async def test_help_formatting_and_presentation(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    # Test formatting of single command (this still works as expected)
    formatted = hc.format_command(commands[0])
    assert "**one**" in formatted and "`usage`" in formatted

    # Formatting a whole page
    page = hc.get_commands_paginator(ctx).get_page(1)
    help_text = hc.format_help_page(page)
    assert "Page 1/" in help_text
    
    # Because sorting is alphabetical, page 1 will contain "five" and "four"
    assert "**five**" in help_text or "**four**" in help_text

    # Request command-specific help
    await hc.show_command_help(ctx, "three")
    ctx.reply.assert_awaited_once()
    sent = ctx.reply.call_args[0][0]
    assert "three" in sent

    # Missing command
    await hc.show_command_help(ctx, "six")
    sent = ctx.reply.call_args[0][0]
    assert "not found" in sent.lower()

    # Page presentation
    await hc.show_help_page(ctx, page_number=2)
    sent = ctx.reply.call_args[0][0]
    assert "Page 2/" in sent


@pytest.mark.asyncio
async def test_execute_dispatch(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    # Passing page number
    await hc.execute(ctx, "2")
    sent = ctx.reply.call_args[0][0]
    assert "Page 2/" in sent

    # Passing command name
    ctx.reply.reset_mock()
    await hc.execute(ctx, "four")
    sent = ctx.reply.call_args[0][0]
    assert "four" in sent


@pytest.mark.asyncio
async def test_execute_no_arg(commands):
    ctx = DummyContext(commands)
    hc = HelpCommand(per_page=2)

    await hc.execute(ctx)  # no argument, should show page 1
    sent = ctx.reply.call_args[0][0]
    assert "Page 1/" in sent
