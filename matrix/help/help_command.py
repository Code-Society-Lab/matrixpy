from typing import Optional, List
from abc import ABC, abstractmethod

from matrix.context import Context
from matrix.command import Command
from matrix.group import Group

from .pagination import Paginator, Page


class HelpCommand(Command, ABC):
    """Abstract base class for help commands with built-in pagination support.

    Subclasses must implement the formatting methods to customize appearance.
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

    @abstractmethod
    def format_help_page(self, page: Page[Command], title: str = "Commands") -> str:
        pass  # pragma: no cover

    @abstractmethod
    def format_subcommand_page(self, page: Page[Command], group_name: str) -> str:
        pass  # pragma: no cover

    @abstractmethod
    def format_command(self, cmd: Command) -> str:
        """Format a single command for display.

        :param cmd: The command to format
        :return: Formatted string representation of the command
        """
        pass  # pragma: no cover

    @abstractmethod
    def format_group(self, group: Group) -> str:  # pragma: no cover
        """Format a group command for display.

        :param group: The group to format
        :return: Formatted string representation of the group
        """
        pass

    @abstractmethod
    def format_subcommand(self, subcommand: Command) -> str:
        """Format a subcommand for display.

        :param subcommand: The subcommand to format
        :return: Formatted string representation of the subcommand
        """
        pass  # pragma: no cover

    @abstractmethod
    def format_page_info(self, page: Page[Command]) -> str:
        """Format the page information display.

        :param page: Page object containing pagination info
        :return: Formatted page information string
        """
        pass  # pragma: no cover

    @abstractmethod
    async def on_command_not_found(self, ctx: Context, command_name: str) -> None:
        """Called when a command is not found."""
        pass  # pragma: no cover

    @abstractmethod
    async def on_subcommand_not_found(
        self, ctx: Context, group: Group, subcommand_name: str
    ) -> None:
        """Called when a subcommand is not found."""
        pass  # pragma: no cover

    @abstractmethod
    async def on_page_out_of_range(
        self, ctx: Context, page_number: int, total_pages: int
    ) -> None:
        """Called when a requested page is out of bounds."""
        pass  # pragma: no cover

    @abstractmethod
    async def on_empty_page(self, ctx: Context) -> None:
        pass  # pragma: no cover

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
        subcommands = list(getattr(group, "commands", {}).values())
        sorted_subcommands = sorted(subcommands, key=lambda c: c.name.lower())

        return Paginator(sorted_subcommands, self.per_page)

    def find_command(self, ctx: Context, command_name: str) -> Optional[Command]:
        """Find a command by name.

        :param ctx: Command context
        :param command_name: Name of the command to find
        :return: Command if found, None otherwise
        """
        return ctx.bot.commands.get(command_name)

    def find_subcommand(self, group: Group, subcommand_name: str) -> Optional[Command]:
        """Find a subcommand within a group.

        :param group: The group to search in
        :param subcommand_name: Name of the subcommand to find
        :return: Subcommand if found, None otherwise
        """
        group_commands = getattr(group, "commands", {})
        return group_commands.get(subcommand_name)

    async def show_command_help(self, ctx: Context, command: Command) -> None:
        """Show help for a specific command (non-group)."""
        await ctx.reply(self.format_command(command))

    async def show_group_help(
        self,
        ctx: Context,
        group: Group,
        subcommand_name: Optional[str] = None,
        page_number: int = 1,
    ) -> None:
        """
        Show help for a group or its subcommand, with optional pagination.
        """
        if subcommand_name:
            subcmd = self.find_subcommand(group, subcommand_name)

            if subcmd:
                await ctx.reply(self.format_subcommand(subcmd))
            else:
                await self.on_subcommand_not_found(ctx, group, subcommand_name)
            return

        # No subcommand: show paginated group subcommands
        group_help = self.format_group(group)
        subcommands = getattr(group, "commands", {})

        if subcommands:
            paginator = self.get_subcommands_paginator(group)
            page = paginator.get_page(page_number)
            subcommand_list = self.format_subcommand_page(page, group.name)

            await ctx.reply(f"{group_help}\n\n{subcommand_list}")
        else:
            await self.on_empty_page(ctx)

    async def show_help_page(self, ctx: Context, page_number: int = 1) -> None:
        """Show a paginated help page for all commands.

        :param ctx: Command context
        :param page_number: Page number to display
        """
        paginator = self.get_commands_paginator(ctx)
        page = paginator.get_page(page_number)
        help_message = self.format_help_page(page)

        await ctx.reply(help_message)

    def parse_help_arguments(
        self, args: List[str]
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

    async def execute(self, ctx: Context, cmd_or_page=None, subcommand=None) -> None:
        """
        Execute the help command using show_command_help and show_group_help.
        """

        args = []

        if cmd_or_page is not None:
            args.append(cmd_or_page)

        if subcommand is not None:
            args.append(subcommand)

        command_name, subcommand_name, page = self.parse_help_arguments(args)

        if command_name:
            cmd = self.find_command(ctx, command_name)

            if not cmd:
                await self.on_command_not_found(ctx, command_name)
                return

            if isinstance(cmd, Group):
                await self.show_group_help(ctx, cmd, subcommand_name)
                return

            if isinstance(cmd, Command):
                await self.show_command_help(ctx, cmd)
                return
        else:
            await self.show_help_page(ctx, page)


class DefaultHelpCommand(HelpCommand):
    """A default implementation of HelpCommand with basic formatting.

    This provides default formatting for commands, groups, and pagination
    that works well for most use cases.
    """

    def format_help_page(self, page: Page[Command], title: str = "Commands") -> str:
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

    def format_subcommand_page(self, page: Page[Command], group_name: str) -> str:
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

    def format_command(self, cmd: Command) -> str:
        """Format a single command for display.

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

        :param group: The group to format
        :return: Formatted string representation of the group
        """
        subcommands_text = ""
        subcommand_count = len(getattr(group, "commands", {}))

        if subcommand_count > 0:
            subcommands_text = f" ({subcommand_count} subcommands)"

        return (
            f"**{group.name}** [GROUP]{subcommands_text}\n"
            f"Usage: `{group.usage}`\n"
            f"Description: {group.description or 'None'}"
        )

    def format_subcommand(self, subcommand: Command) -> str:
        """Format a subcommand for display.

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

        :param page: Page object containing pagination info
        :return: Formatted page information string
        """
        return f"**Page {page.page_number}/{page.total_pages}**"

    async def on_command_not_found(self, ctx: Context, command_name: str) -> None:
        await ctx.reply(f"Command `{command_name}` not found.")

    async def on_subcommand_not_found(
        self, ctx: Context, group: Group, subcommand_name: str
    ) -> None:
        await ctx.reply(
            f"Subcommand `{subcommand_name}` not found " f"in group `{group.name}`."
        )

    async def on_empty_page(self, ctx: Context) -> None:
        await ctx.reply("No commands.")

    async def on_page_out_of_range(
        self, ctx: Context, page_number: int, total_pages: int
    ) -> None:
        await ctx.reply(f"Page {page_number} does not exist.")
