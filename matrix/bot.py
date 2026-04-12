import time
import inspect
import asyncio
import logging

from typing import Optional, Any

from nio import AsyncClient, Event, MatrixRoom

from .room import Room
from .group import Group
from .config import Config
from .context import Context
from .extension import Extension
from .registry import Registry
from .help import HelpCommand, DefaultHelpCommand
from .scheduler import Scheduler
from .errors import (
    AlreadyRegisteredError,
    CommandNotFoundError,
    CheckError,
    RoomNotFoundError,
)


class Bot(Registry):
    """
    The base class defining a Matrix bot.

    This class manages the connection to a Matrix homeserver, listens
    for events, and dispatches them to registered handlers. It also supports
    a command system with decorators for easy registration.
    """

    def __init__(
        self,
        *,
        help_: Optional[HelpCommand] = None,
    ) -> None:
        super().__init__(self.__class__.__name__)

        self._config: Config | None = None
        self._client: AsyncClient | None = None
        self._synced: asyncio.Event = asyncio.Event()
        self._help: HelpCommand | None = help_

        self.extensions: dict[str, Extension] = {}
        self.scheduler: Scheduler = Scheduler()
        self.log: logging.Logger = logging.getLogger(__name__)
        self.start_at: float | None = None

    @property
    def client(self) -> AsyncClient:
        assert self._client is not None, "Bot has not been started."
        return self._client

    @property
    def config(self) -> Config:
        assert self._config is not None, "Bot has not been started."
        return self._config

    @property
    def help(self) -> HelpCommand:
        assert self._help is not None, "Bot has not been started."
        return self._help

    def _auto_register_events(self) -> None:
        for attr in dir(self):
            if not attr.startswith("on_"):
                continue

            coro = getattr(self, attr, None)
            if not inspect.iscoroutinefunction(coro):
                continue

            try:
                if attr in self.LIFECYCLE_EVENTS:
                    self.hook(coro)

                if attr in self.EVENT_MAP:
                    self.event(coro)
            except ValueError:
                continue

    def get_room(self, room_id: str) -> Room | None:
        """Retrieve a `Room` instance by its Matrix room ID.

        Returns the `Room` object corresponding to `room_id` if it exists in
        the client's known rooms. Returns `None` if the room cannot be found.

        ## Example

        ```python
        room = bot.get_room("!abc123:matrix.org")
        if room:
            print(room.name)
        ```
        """
        if matrix_room := self.client.rooms.get(room_id):
            return Room(matrix_room=matrix_room, client=self.client)
        return None

    def load_extension(self, extension: Extension) -> None:
        self.log.debug(f"Loading extension: '{extension.name}'")

        if extension.name in self.extensions:
            raise AlreadyRegisteredError(extension)

        for cmd in extension._commands.values():
            if isinstance(cmd, Group):
                self.register_group(cmd)
            else:
                self.register_command(cmd)

        for event_type, handlers in extension._event_handlers.items():
            self._event_handlers[event_type].extend(handlers)

        for hook_name, handlers in extension._hook_handlers.items():
            self._hook_handlers[hook_name].extend(handlers)

        self._checks.extend(extension._checks)
        self._error_handlers.update(extension._error_handlers)
        self._command_error_handlers.update(extension._command_error_handlers)

        for job in extension._scheduler.jobs:
            self.scheduler.scheduler.add_job(
                job.func,
                trigger=job.trigger,
                name=job.name,
            )

        self.extensions[extension.name] = extension
        extension.load(self)
        self.log.debug("loaded extension '%s'", extension.name)

    def unload_extension(self, ext_name: str) -> None:
        self.log.debug("Unloading extension: '%s'", ext_name)

        extension = self.extensions.pop(ext_name, None)
        if extension is None:
            raise ValueError(f"No extension named '{ext_name}' is loaded")

        for cmd_name in extension._commands:
            self._commands.pop(cmd_name, None)

        for event_type, handlers in extension._event_handlers.items():
            for handler in handlers:
                self._event_handlers[event_type].remove(handler)

        for check in extension._checks:
            self._checks.remove(check)

        for exc_type in extension._error_handlers:
            self._error_handlers.pop(exc_type, None)

        for exc_type in extension._command_error_handlers:
            self._command_error_handlers.pop(exc_type, None)

        for job in extension._scheduler.jobs:
            bot_job = next((j for j in self.scheduler.jobs if j.func is job.func), None)
            if bot_job:
                bot_job.remove()

        extension.unload()
        self.log.debug("unloaded extension '%s'", ext_name)

    # LIFECYCLE

    async def on_ready(self) -> None:
        """Override this in a subclass."""
        pass

    async def _on_ready(self) -> None:
        """Internal hook — always fires, calls public override then extension handlers."""
        await self.on_ready()
        await self._dispatch("on_ready")

    async def on_error(self, error: Exception) -> None:
        """Override this in a subclass."""
        self.log.exception("Unhandled error: '%s'", error)

    async def _on_error(self, error: Exception) -> None:
        if handler := self._error_handlers.get(type(error)):
            await handler(error)
            return

        if self._fallback_error_handler:
            await self._fallback_error_handler(error)
            return

        await self._dispatch("on_error", error)

    async def on_command(self, _ctx: Context) -> None:
        """Override this in a subclass."""
        pass

    async def _on_command(self, ctx: Context) -> None:
        await self._dispatch("on_command", ctx)

    async def on_command_error(self, _ctx: Context, error: Exception) -> None:
        """Override this in a subclass."""
        self.log.exception("Unhandled error: '%s'", error)

    async def _on_command_error(self, ctx: Context, error: Exception) -> None:
        """
        Handles errors raised during command invocation.

        This method is called automatically when a command error occurs.
        If a specific error handler is registered for the type of the
        exception, it will be invoked with the current context and error.
        """
        if handler := self._command_error_handlers.get(type(error)):
            await handler(ctx, error)
            return

        await self._dispatch("on_command_error", ctx, error)

    # ENTRYPOINT

    def _load_config(self, config: Config | str) -> None:
        if self._config is not None:
            raise RuntimeError("Config is already loaded.")

        if isinstance(config, str):
            config = Config(config_path=config)
        elif not isinstance(config, Config):
            raise TypeError("config must be a Config instance or a config file path")

        self._config = config
        self._client = AsyncClient(config.homeserver)
        self._help = self._help or DefaultHelpCommand()

        self.prefix = config.prefix
        self.register_command(self.help)

        self.client.add_event_callback(self._on_matrix_event, Event)
        self._auto_register_events()

    def start(self, *, config: Config | str) -> None:
        """
        Synchronous entry point for running the bot.

        This is a convenience wrapper that allows running the bot like a
        script using a blocking call. It internally calls :meth:`run` within
        :func:`asyncio.run`, and ensures the client is closed gracefully
        on interruption.
        """
        self._load_config(config)

        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.log.info("bot interrupted by user")
        finally:
            asyncio.run(self.client.close())

    async def run(self) -> None:
        """
        Log in to the Matrix homeserver and begin syncing events.

        This method should be used within an asynchronous context,
        typically via :func:`asyncio.run`. It handles authentication,
        calls the :meth:`on_ready` hook, and starts the long-running
        sync loop for receiving events.
        """
        self.client.user = self.config.username

        self.start_at = time.time()
        self.log.info("starting – timestamp=%s", self.start_at)

        if self.config.token:
            self.client.access_token = self.config.token
        else:
            login_resp = await self.client.login(self.config.password)
            self.log.info("logged in: %s", login_resp)

        sync_task = asyncio.create_task(self.client.sync_forever(timeout=30_000))

        await self._wait_until_synced()
        await self._on_ready()

        self.scheduler.start()
        await sync_task

    async def _wait_until_synced(self) -> None:
        await self._synced.wait()

    # MATRIX EVENTS

    async def on_message(self, room: Room, event: Event) -> None:
        await self._process_commands(room, event)

    async def _on_matrix_event(self, matrix_room: MatrixRoom, event: Event) -> None:
        if not self._synced.is_set():
            self._synced.set()

        # ignore bot events
        if event.sender == self.client.user:
            return

        # ignore events that happened before the bot started
        if self.start_at and self.start_at > (event.server_timestamp / 1000):
            return

        try:
            room = self.get_room(matrix_room.room_id)

            if not room:
                raise RoomNotFoundError(f"Room '{matrix_room.room_id}' not found.")

            await self._dispatch_matrix_event(room, event)
        except Exception as error:
            await self._on_error(error)

    async def _dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Fire all listeners registered for a named lifecycle event."""
        for handler in self._hook_handlers.get(event_name, []):
            await handler(*args, **kwargs)

    async def _dispatch_matrix_event(self, room: Room, event: Event) -> None:
        """Fire all listeners registered for a named matrix event."""
        for event_type, funcs in self._event_handlers.items():
            if isinstance(event, event_type):
                for func in funcs:
                    await func(room, event)

    async def _process_commands(self, room: Room, event: Event) -> None:
        """Parse and execute commands"""
        try:
            ctx = await self._build_context(room, event)

            if ctx.command:
                for check in self._checks:
                    if not await check(ctx):
                        raise CheckError(ctx.command, check)

                await self._on_command(ctx)
                await ctx.command(ctx)
        except Exception as error:
            ctx = Context(bot=self, room=room, event=event)
            await self._on_command_error(ctx, error)

    async def _build_context(self, matrix_room: Room, event: Event) -> Context:
        room = self.get_room(matrix_room.room_id)

        if not room:
            raise RoomNotFoundError(f"Room '{matrix_room.room_id}' not found.")

        ctx = Context(bot=self, room=room, event=event)
        prefix = self.prefix or self.config.prefix

        if not ctx.body.startswith(prefix):
            return ctx

        if parts := ctx.body[len(prefix) :].split():
            cmd_name = parts[0]
            cmd = self._commands.get(cmd_name)

            if not cmd:
                raise CommandNotFoundError(cmd_name)

            ctx.command = cmd

        return ctx
