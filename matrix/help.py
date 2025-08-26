from typing import Optional, List, TypeVar, Generic, Union

from .context import Context
from .command import Command
from .group import Group


T = TypeVar('T')


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

    def get_page(self, page_number: int) -> 'Page[T]':
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
            total_items=self.total_items
        )

    def get_pages(self) -> List['Page[T]']:
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
        total_items: int
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

    Supports both regular commands and group with proper formatting.

    - To customize formatting, override the format_command() or format_group()
        methods.
    - To customize pagination display, override the format_page_info() method.
    """

    DEFAULT_PER_PAGE = 5

    def __init__(
        self,
        prefix: Optional[str] = None,
        per_page: int = DEFAULT_PER_PAGE
    ):
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

    def format_group(self, group: Group) -> str:
        """Format a group command for display.

        Override this method to customize group formatting.

        :param group: The group to format
        :return: Formatted string representation of the group
        """
        subcommands_text = ""
        subcommand_count = len(getattr(group, 'commands', {}))

        if subcommand_count > 0:
            subcommands_text = f" ({subcommand_count} subcommands)"

        return (
            f"**{group.name}** [GROUP]{subcommands_text}\n"
            f"Usage: `{group.usage}`\n"
            f"Description: {group.description or 'None'}"
        )

    def format_subcommand(self, subcommand: Command) -> str:
        """Format a subcommand for display.

        Override this method to customize subcommand formatting.

        :param subcommand: The subcommand to format
        :return: Formatted string representation of the subcommand
        """
        return (
            f"**{subcommand.name}**\n"
            f"Usage: `{subcommand.usage}`\n"
            f"Description: {subcommand.description or 'None'}"
        )

    def format_page_info(self, page: Page[Command]) -> str:
        """Format the page information display.

        Override this method to customize pagination display.

        :param page: Page object containing pagination info
        :return: Formatted page information string
        """
        return f"**Page {page.page_number}/{page.total_pages}**"

    def format_help_page(
        self,
        page: Page[Command],
        title: str = "Commands"
    ) -> str:
        """Format a complete help page.

        :param page: Page object containing commands and pagination info
        :param title: Title for the help page
        :return: Complete formatted help page
        """
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
        """Format a complete subcommand help page.

        :param page: Page object containing subcommands and pagination info
        :param group_name: Name of the parent group
        :return: Complete formatted subcommand help page
        """
        help_entries = []

        if not page.items:
            return f"No subcommands available for group `{group_name}`."

        for subcmd in page.items:
            help_entries.append(self.format_subcommand(subcmd))

        help_text = "\n\n".join(help_entries)
        page_info = self.format_page_info(page)

        return f"**{group_name} Subcommands**\n\n{help_text}\n\n{page_info}"

    def get_commands_paginator(self, ctx: Context) -> Paginator[Command]:
        """Get a paginator for all commands.

        :param ctx: Command context
        :return: Paginator configured with all commands
        """
        all_commands = list(ctx.bot.commands.values())
        sorted_commands = sorted(all_commands, key=lambda c: c.name.lower())

        return Paginator(sorted_commands, self.per_page)

    def get_subcommands_paginator(self, group: Group) -> Paginator[Command]:
        """Get a paginator for all subcommands in a group.

        :param group: The group to get subcommands from
        :return: Paginator configured with all subcommands
        """
        subcommands = list(getattr(group, 'commands', {}).values())
        sorted_subcommands = sorted(subcommands, key=lambda c: c.name.lower())

        return Paginator(sorted_subcommands, self.per_page)

    def find_command(
        self,
        ctx: Context,
        command_name: str
    ) -> Optional[Command]:
        """Find a command by name.

        :param ctx: Command context
        :param command_name: Name of the command to find
        :return: Command if found, None otherwise
        """
        return ctx.bot.commands.get(command_name)

    def find_subcommand(
        self,
        group: Group,
        subcommand_name: str
    ) -> Optional[Command]:
        """Find a subcommand within a group.

        :param group: The group to search in
        :param subcommand_name: Name of the subcommand to find
        :return: Subcommand if found, None otherwise
        """
        group_commands = getattr(group, 'commands', {})
        return group_commands.get(subcommand_name)

    async def show_command_help(
        self,
        ctx: Context,
        command_name: str,
        subcommand_name: Optional[str] = None
    ) -> None:
        """Show help for a specific command or subcommand.

        :param ctx: Command context
        :param command_name: Name of the command to show help for
        :param subcommand_name: Name of the subcommand
        """
        cmd = self.find_command(ctx, command_name)

        if not cmd:
            await ctx.reply(f"Command `{command_name}` not found.")
            return

        if not subcommand_name:
            if isinstance(cmd, Group):
                group_help = self.format_group(cmd)
                subcommands = getattr(cmd, 'commands', {})

                if subcommands:
                    paginator = self.get_subcommands_paginator(cmd)
                    first_page = paginator.get_page(1)
                    subcommand_list = self.format_subcommand_page(
                        first_page,
                        cmd.name
                    )
                    help_message = f"{group_help}\n\n{subcommand_list}"
                else:
                    help_message = f"{group_help}\n\nNo subcommands available."

                await ctx.reply(help_message)
            else:
                await ctx.reply(self.format_command(cmd))
            return

        if not isinstance(cmd, Group):
            await ctx.reply(f"Command `{command_name}` is not a group.")
            return

        if subcommand := self.find_subcommand(cmd, subcommand_name):
            await ctx.reply(self.format_subcommand(subcommand))
        else:
            await ctx.reply(
                f"Subcommand `{subcommand_name}` not " /
                f"found in group `{command_name}`."
            )

    async def show_help_page(self, ctx: Context, page_number: int = 1) -> None:
        """Show a paginated help page for all commands.

        :param ctx: Command context
        :param page_number: Page number to display
        """
        paginator = self.get_commands_paginator(ctx)
        page = paginator.get_page(page_number)
        help_message = self.format_help_page(page)

        await ctx.reply(help_message)

    async def show_subcommand_page(
        self,
        ctx: Context,
        group_name: str,
        page_number: int = 1
    ) -> None:
        """Show a paginated help page for group subcommands.

        :param ctx: Command context
        :param group_name: Name of the group
        :param page_number: Page number to display
        """
        group = self.find_command(ctx, group_name)

        if not group:
            await ctx.reply(f"Group `{group_name}` not found.")
            return

        if not isinstance(group, Group):
            await ctx.reply(f"Command `{group_name}` is not a group.")
            return

        paginator = self.get_subcommands_paginator(group)
        page = paginator.get_page(page_number)
        help_message = self.format_subcommand_page(page, group_name)

        await ctx.reply(help_message)

    def parse_help_arguments(
        self,
        args: List[str]
    ) -> tuple[Optional[str], Optional[str], int]:
        """Parse help command arguments to determine what to show.

        :param args: List of arguments passed to help command
        :return: Tuple of (command_name, subcommand_name, page_number)
        """
        command_name = None
        subcommand_name = None
        page_number = 1

        if not args:
            return command_name, subcommand_name, page_number

        # Check if first argument is a page number
        if len(args) == 1 and args[0].isdigit():
            page_number = int(args[0])
            return command_name, subcommand_name, page_number

        command_name = args[0]

        if len(args) >= 2:
            if args[1].isdigit():
                page_number = int(args[1])
            else:
                subcommand_name = args[1]

                if len(args) >= 3 and args[2].isdigit():
                    page_number = int(args[2])

        return command_name, subcommand_name, page_number

    async def execute(
        self,
        ctx: Context,
        cmd_or_page=None,
        subcommand=None
    ) -> None:
        """Execute the help command.

        Usage patterns:
        - `help` - Show first page of all commands
        - `help 2` - Show page 2 of all commands
        - `help ping` - Show help for specific command
        - `help group` - Show help for group with first page of subcommands
        - `help group subcmd` - Show help for specific subcommand
        - `help group 2` - Show page 2 of group's subcommands

        :param ctx: Command context
        :param cmd_or_page: Command name or page number
        :param subcommand: Subcommand name or page number for groups
        """
        # Convert arguments to list for parsing
        args = []
        if cmd_or_page is not None:
            args.append(cmd_or_page)
        if subcommand is not None:
            args.append(subcommand)

        command_name, subcommand_name, page = self.parse_help_arguments(args)

        if command_name:
            if subcommand_name and not subcommand_name.isdigit():
                await self.show_command_help(
                    ctx,
                    command_name,
                    subcommand_name
                )
            else:
                cmd = self.find_command(ctx, command_name)

                if cmd and isinstance(cmd, Group) and subcommand_name is None:
                    await self.show_subcommand_page(ctx, command_name, page)
                else:
                    await self.show_command_help(ctx, command_name)
        else:
            await self.show_help_page(ctx, page)
