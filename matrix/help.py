from typing import Optional, List, TypeVar, Generic

from .context import Context
from .command import Command


T = TypeVar("T")


class Paginator(Generic[T]):
    """A generic paginator for any list of items."""

    def __init__(self, items: List[T], per_page: int = 5):
        """Initialize the paginator.

        :param items: List of items to paginate
        :param per_page: Number of items per page
        """
        self.items = items
        self.per_page = per_page
        self.total_items = len(items)
        self.total_pages = max(1, -(-self.total_items // self.per_page))

    def get_page(self, page_number: int) -> "Page[T]":
        """Get a specific page of items.

        :param page_number: Page number to retrieve (1-indexed)
        :return: Page object containing items and metadata
        """
        # Clamp page number to valid range
        page_number = max(1, min(page_number, self.total_pages))

        start_idx = (page_number - 1) * self.per_page
        end_idx = start_idx + self.per_page

        return Page(
            items=self.items[start_idx:end_idx],
            page_number=page_number,
            total_pages=self.total_pages,
            per_page=self.per_page,
            total_items=self.total_items,
        )

    def get_pages(self) -> List["Page[T]"]:
        """Get all pages.

        :return: List of all pages
        """
        return [self.get_page(i) for i in range(1, self.total_pages + 1)]


class Page(Generic[T]):
    """Represents a single page of paginated items."""

    def __init__(
        self,
        items: List[T],
        page_number: int,
        total_pages: int,
        per_page: int,
        total_items: int,
    ):
        """Initialize a page.

        :param items: Items on this page
        :param page_number: Current page number
        :param total_pages: Total number of pages
        :param per_page: Items per page
        :param total_items: Total number of items across all pages
        """
        self.items = items
        self.page_number = page_number
        self.total_pages = total_pages
        self.per_page = per_page
        self.total_items = total_items

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page_number > 1

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page_number < self.total_pages

    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number."""
        return self.page_number - 1 if self.has_previous else None

    @property
    def next_page(self) -> Optional[int]:
        """Get next page number."""
        return self.page_number + 1 if self.has_next else None


class HelpCommand(Command):
    """A reusable help command with built-in pagination support.

    To customize formatting, override the format_command() method.
    To customize pagination display, override the format_page_info() method.
    """

    DEFAULT_PER_PAGE = 5

    def __init__(self, prefix: Optional[str] = None, per_page: int = DEFAULT_PER_PAGE):
        """Initialize the help command.

        :param prefix: Command prefix override
        :param per_page: Number of commands to display per page
        """
        super().__init__(
            self.execute,
            name="help",
            description="Sends the command help.",
            prefix=prefix,
        )
        self.per_page = per_page

    def format_command(self, cmd: Command) -> str:
        """Format a single command for display.

        Override this method to customize command formatting.

        :param cmd: The command to format
        :return: Formatted string representation of the command
        """
        return (
            f"**{cmd.name}**\n"
            f"Usage: `{cmd.usage}`\n"
            f"Description: {cmd.description or 'None'}"
        )

    def format_page_info(self, page: Page[Command]) -> str:
        """Format the page information display.

        Override this method to customize pagination display.

        :param page: Page object containing pagination info
        :return: Formatted page information string
        """
        return f"**Page {page.page_number}/{page.total_pages}**"

    def format_help_page(self, page: Page[Command]) -> str:
        """Format a complete help page.

        :param page: Page object containing commands and pagination info
        :return: Complete formatted help page
        """
        if not page.items:
            return "No commands available."

        help_entries = "\n\n".join(self.format_command(cmd) for cmd in page.items)
        page_info = self.format_page_info(page)

        return f"{help_entries}\n\n{page_info}"

    def get_commands_paginator(self, ctx: Context) -> Paginator[Command]:
        """Get a paginator for all commands.

        :param ctx: Command context
        :return: Paginator configured with all commands
        """
        all_commands = list(ctx.bot.commands.values())
        sorted_commands = sorted(all_commands, key=lambda c: c.name.lower())

        return Paginator(sorted_commands, self.per_page)

    def find_command(self, ctx, command_name: str) -> Optional[Command]:
        """Find a command by name.

        :param ctx: Command context
        :param command_name: Name of the command to find
        :return: Command if found, None otherwise
        """
        return ctx.bot.commands.get(command_name)

    async def show_command_help(self, ctx, command_name: str) -> None:
        """Show help for a specific command.

        :param ctx: Command context
        :param command_name: Name of the command to show help for
        """
        cmd = self.find_command(ctx, command_name)

        if cmd:
            await ctx.reply(self.format_command(cmd))
        else:
            await ctx.reply(f"Command `{command_name}` not found.")

    async def show_help_page(self, ctx, page_number: int = 1) -> None:
        """Show a paginated help page.

        :param ctx: Command context
        :param page_number: Page number to display
        """
        paginator = self.get_commands_paginator(ctx)
        page = paginator.get_page(page_number)
        help_message = self.format_help_page(page)

        await ctx.reply(help_message)

    async def execute(self, ctx: Context, arg=None) -> None:  # type: ignore
        """Execute the help command.

        Note: For now we ignore the arg type since it's the only way
              to do different actions depending on the type of the function
              without causing errors.

        Usage patterns:
        - `help` - Show first page of all commands
        - `help 2` - Show page 2 of all commands
        - `help ping` - Show help for specific command

        :param ctx: Command context
        :param arg: Command name or Page number
        """
        page = 1
        command_name = None

        if isinstance(arg, str):
            if arg.isdigit():
                page = int(arg)
            else:
                command_name = arg.strip()

        if command_name:
            await self.show_command_help(ctx, arg)
        else:
            await self.show_help_page(ctx, page)
