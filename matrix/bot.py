import time
import inspect
import asyncio
import logging

from typing import Union, Optional

from nio import AsyncClient, Event, MatrixRoom

from .room import Room
from .group import Group
from .config import Config
from .context import Context
from .extension import Extension
from .registry import Registry
from .help import HelpCommand, DefaultHelpCommand
from .scheduler import Scheduler
from .errors import AlreadyRegisteredError, CommandNotFoundError, CheckError


class Bot(Registry):
    """
    The base class defining a Matrix bot.

    This class manages the connection to a Matrix homeserver, listens
    for events, and dispatches them to registered handlers. It also supports
    a command system with decorators for easy registration.
    """

    def __init__(
        self, *, config: Union[Config, str], help: Optional[HelpCommand] = None
    ) -> None:
        if isinstance(config, Config):
            self.config = config
        elif isinstance(config, str):
            self.config = Config(config_path=config)
        else:
            raise TypeError("config must be a Config instance or a config file path")

        super().__init__(self.__class__.__name__, prefix=self.config.prefix)

        self.client: AsyncClient = AsyncClient(self.config.homeserver)
        self.extensions: dict[str, Extension] = {}
        self.scheduler: Scheduler = Scheduler()
        self.log: logging.Logger = logging.getLogger(__name__)

        self.start_at: float | None = None  # unix timestamp

        self.help: HelpCommand = help or DefaultHelpCommand(prefix=self.prefix)
        self.register_command(self.help)

        self.client.add_event_callback(self._on_event, Event)
        self._auto_register_events()

    def get_room(self, room_id: str) -> Room:
        """Retrieve a Room instance based on the room_id."""
        matrix_room = self.client.rooms[room_id]
        return Room(matrix_room=matrix_room, client=self.client)

    def load_extension(self, extension: Extension) -> None:
        self.log.info(f"Loading extension: '{extension.name}'")

        if extension.name in self.extensions:
            raise AlreadyRegisteredError(extension)

        for cmd in extension._commands.values():
            if isinstance(cmd, Group):
                self.register_group(cmd)
            else:
                self.register_command(cmd)

        for event_type, handlers in extension._event_handlers.items():
            self._event_handlers[event_type].extend(handlers)

        self._checks.extend(extension._checks)
        self._error_handlers.update(extension._error_handlers)
        self._command_error_handlers.update(extension._command_error_handlers)

        for job in extension._scheduler.jobs:
            self.scheduler.schedule(job.cron, job.func)

        self.extensions[extension.name] = extension
        self.log.info("loaded extension '%s'", extension.name)

    def unload_extension(self, ext_name: str) -> None:
        pass

    def _auto_register_events(self) -> None:
        for attr in dir(self):
            if not attr.startswith("on_"):
                continue
            coro = getattr(self, attr, None)
            if inspect.iscoroutinefunction(coro):
                try:
                    self.event(coro)
                except ValueError:  # ignore unknown name
                    continue

    async def _on_event(self, room: MatrixRoom, event: Event) -> None:
        # ignore bot events
        if event.sender == self.client.user:
            return

        # ignore events that happened before the bot started
        if self.start_at and self.start_at > (event.server_timestamp / 1000):
            return

        try:
            await self._dispatch(room, event)
        except Exception as error:
            await self.on_error(error)

    async def _dispatch(self, room: MatrixRoom, event: Event) -> None:
        """Internal type-based fan-out plus optional command handling."""
        for event_type, funcs in self._event_handlers.items():
            if isinstance(event, event_type):
                for func in funcs:
                    await func(room, event)

    async def _process_commands(self, room: MatrixRoom, event: Event) -> None:
        """Parse and execute commands"""
        ctx = await self._build_context(room, event)

        if ctx.command:
            for check in self._checks:
                if not await check(ctx):
                    raise CheckError(ctx.command, check)

            await ctx.command(ctx)

    async def _build_context(self, matrix_room: MatrixRoom, event: Event) -> Context:
        """Builds the base context and extracts the command from the event"""
        room = self.get_room(matrix_room.room_id)
        ctx = Context(bot=self, room=room, event=event)

        if ctx.body.startswith(self.prefix):
            prefix = self.prefix
        else:
            prefix = next(
                (cmd.prefix for cmd in self._commands.values() if cmd.prefix and ctx.body.startswith(cmd.prefix)),
                None,
            )

        if prefix is None:
            return ctx

        if parts := ctx.body[len(prefix):].split():
            cmd_name = parts[0]
            cmd = self._commands.get(cmd_name)

            if cmd and cmd.prefix:
                if not ctx.body.startswith(cmd.prefix):
                    return ctx

            if not cmd:
                raise CommandNotFoundError(cmd_name)

            ctx.command = cmd

        return ctx

    async def on_message(self, room: MatrixRoom, event: Event) -> None:
        """
        Invoked when a message event is received.

        This method is automatically called when a :class:`nio.RoomMessageText`
        event is detected. It is primarily responsible for detecting and
        processing commands that match the bot's defined prefix.

        :param ctx: The context object containing information about the Matrix
                    room and the message event.
        :type ctx: Context
        """
        await self._process_commands(room, event)

    async def on_ready(self) -> None:
        """Invoked after a successful login, before sync starts."""
        self.log.info("bot is ready")

    async def on_error(self, error: Exception) -> None:
        """
        Handle errors by invoking a registered error handler,
        a generic error callback, or logging the exception.

        :param error: The exception instance that was raised.
        :type error: Exceptipon
        """
        if handler := self._error_handlers.get(type(error)):
            await handler(error)
            return

        if self._on_error:
            await self._on_error(error)
            return
        self.log.exception("Unhandled error: '%s'", error)

    async def on_command_error(self, ctx: "Context", error: Exception) -> None:
        """
        Handles errors raised during command invocation.

        This method is called automatically when a command error occurs.
        If a specific error handler is registered for the type of the
        exception, it will be invoked with the current context and error.

        :param ctx: The context in which the command was invoked.
        :type ctx: Context
        :param error: The exception that was raised during command execution.
        :type error: Exception
        """
        if handler := self._command_error_handlers.get(type(error)):
            await handler(ctx, error)

    async def run(self) -> None:
        """
        Log in to the Matrix homeserver and begin syncing events.

        This method should be used within an asynchronous context,
        typically via :func:`asyncio.run`. It handles authentication,
        calls the :meth:`on_ready` hook, and starts the long-running
        sync loop for receiving events.
        """
        self.client.user = self.config.user_id

        self.start_at = time.time()
        self.log.info("starting – timestamp=%s", self.start_at)

        if self.config.token:
            self.client.access_token = self.config.token
        else:
            login_resp = await self.client.login(self.config.password)
            self.log.info("logged in: %s", login_resp)

        self.scheduler.start()

        await self.on_ready()
        await self.client.sync_forever(timeout=30_000)

    def start(self) -> None:
        """
        Synchronous entry point for running the bot.

        This is a convenience wrapper that allows running the bot like a
        script using a blocking call. It internally calls :meth:`run` within
        :func:`asyncio.run`, and ensures the client is closed gracefully
        on interruption.
        """
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.log.info("bot interrupted by user")
        finally:
            asyncio.run(self.client.close())
