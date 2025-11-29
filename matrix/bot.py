import time
import asyncio
import logging

from collections import defaultdict
from typing import (
    Any,
    Dict,
    List,
    Type,
    Union,
    Optional,
    Callable,
    Coroutine,
)

from nio import (
    AsyncClient,
    Event,
    MatrixRoom,
    RoomMessageText,
    RoomMemberEvent,
    TypingNoticeEvent,
    ReactionEvent,
)

from .room import Room
from .group import Group
from .config import Config
from .context import Context
from .command import Command
from .help import HelpCommand, DefaultHelpCommand
from .scheduler import Scheduler

from .errors import (
    AlreadyRegisteredError,
    CommandNotFoundError,
    CheckError,
    GroupAlreadyRegisteredError
)


Callback = Callable[..., Coroutine[Any, Any, Any]]
GroupCallable = Callable[[Callable[..., Coroutine[Any, Any, Any]]], Group]
ErrorCallback = Callable[[Exception], Coroutine]
CommandErrorCallback = Callable[["Context", Exception], Coroutine[Any, Any, Any]]


class Bot:
    """
    The base class defining a Matrix bot.

    This class manages the connection to a Matrix homeserver, listens
    for events, and dispatches them to registered handlers. It also supports
    a command system with decorators for easy registration.

    :param config: Configuration for Matrix client settings
    :type config: Config

    :raises TypeError: If an event or command handler is not a coroutine.
    :raises ValueError: If an unknown event name
    :raises AlreadyRegisteredError: If a new command is already registered.
    """

    EVENT_MAP: Dict[str, Type[Event]] = {
        "on_typing":        TypingNoticeEvent,
        "on_message":       RoomMessageText,
        "on_react":         ReactionEvent,
        "on_member_join":   RoomMemberEvent,
        "on_member_leave":  RoomMemberEvent,
        "on_member_invite": RoomMemberEvent,
        "on_member_ban":    RoomMemberEvent,
        "on_member_kick":   RoomMemberEvent,
        "on_member_change": RoomMemberEvent,
    }

    def __init__(
        self,
        config: Optional[Union[Config, str]] = None,
        **kwargs
    ) -> None:
        if isinstance(config, Config):
            self.config = config
        elif isinstance(config, str):
            self.config = Config(config_path=config)
        else:
            self.config = Config(**kwargs)

        self.client: AsyncClient = AsyncClient(self.config.homeserver)
        self.log: logging.Logger = logging.getLogger(__name__)

        self.prefix: str = self.config.prefix
        self.start_at: float | None = None  # unix timestamp

        self.commands: Dict[str, Command] = {}
        self.checks: List[Callback] = []
        self.scheduler = Scheduler()

        self._handlers: Dict[Type[Event], List[Callback]] = defaultdict(list)
        self._on_error: Optional[ErrorCallback] = None
        self._error_handlers: dict[type[Exception], ErrorCallback] = {}
        self._command_error_handlers: dict[
            type[Exception], CommandErrorCallback
        ] = {}

        self.help: HelpCommand = kwargs.get(
            "help",
            DefaultHelpCommand(prefix=self.prefix)
        )
        self.register_command(self.help)

        self.client.add_event_callback(self._on_event, Event)
        self._auto_register_events()

    def check(self, func: Callback) -> None:
        """
        Register a check callback

        :param func: The check callback
        :type func: Callback

        :raises TypeError: If the function is not a coroutine.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Checks must be coroutine")

        self.checks.append(func)

    def event(
        self,
        func: Optional[Callback] = None,
        *,
        event_spec: Union[str, Type[Event], None] = None,
    ) -> Union[Callback, Callable[[Callback], Callback]]:
        """
        Decorator to register a coroutine as an event handler.

        Can be used with or without arguments:

        - Without arguments, registers based on coroutine name
          lookup in ``EVENT_MAP``::

            @bot.event
            async def on_message(room, event):
                ...

        - With an explicit event type or event name::

            @bot.event(event_spec=RoomMemberEvent)
            async def handle_member(room, event):
                ...

            @bot.event(event_spec="on_member_join")
            async def welcome(room, event):
                ...

        :param func: The coroutine function to register (used when decorator
            is applied without parentheses).
        :type func: coroutine function, optional
        :param event_spec: The event to register for, either as a string key
            matching ``EVENT_MAP`` or a specific event class. If omitted,
            the event type is inferred from the coroutine function's name.
        :type event_spec: str or type or None, optional
        :raises TypeError: If the decorated function is not a coroutine.
        :raises ValueError: If the event name or string is unknown.
        :return: Decorator that registers the event handler.
        :rtype: Callable[[Callable[..., Awaitable[None]]],
                Callable[..., Awaitable[None]]]
        """
        def wrapper(f: Callback) -> Callback:
            if not asyncio.iscoroutinefunction(f):
                raise TypeError("Event handlers must be coroutines")

            if event_spec:
                if isinstance(event_spec, str):
                    event_type = self.EVENT_MAP.get(event_spec)
                    if event_type is None:
                        raise ValueError(f"Unknown event string: {event_spec}")
                else:
                    event_type = event_spec
            else:
                event_type = self.EVENT_MAP.get(f.__name__)
                if event_type is None:
                    raise ValueError(f"Unknown event name: {f.__name__}")

            self._handlers[event_type].append(f)
            self.log.debug(
                "registered event %s for %s",
                f.__name__,
                event_type.__name__
            )
            return f

        if func is None:
            return wrapper

        return wrapper(func)

    def command(
        self,
        name: Optional[str] = None,
        **kwargs
    ) -> Callable[[Callback], Command]:
        """
        Decorator to register a coroutine function as a command handler.

        The command name defaults to the function name unless
        explicitly provided.

        :raises TypeError: If the decorated function is not a coroutine.
        :raises ValueError: If a command with the same name is registered.
        :return: Decorator that registers the command handler.
        :rtype: Callback
        """
        def wrapper(func: Callback) -> Command:
            cmd = Command(func, name=name, prefix=self.prefix, **kwargs)
            return self.register_command(cmd)
        return wrapper

    def schedule(self, cron: str):
        """
        Decorator to register a coroutine function as a scheduled task.

        The cron string defines the schedule for the task.

        :param cron: The cron string defining the schedule.
        :type cron: str
        :raises TypeError: If the decorated function is not a coroutine.
        :return: Decorator that registers the scheduled task.
        :rtype: Callback
        """
        def wrapper(f: Callback) -> Callback:
            if not asyncio.iscoroutinefunction(f):
                raise TypeError("Scheduled tasks must be coroutines")

            self.scheduler.schedule(cron, f)
            self.log.debug(
                "registered scheduled task %s for cron %s",
                f.__name__,
                cron
            )
            return f

        return wrapper

    def register_command(self, cmd: Command) -> Command:
        if cmd in self.commands:
            raise AlreadyRegisteredError(cmd)

        self.commands[cmd.name] = cmd
        self.log.debug("command '%s' registered", cmd)

        return cmd

    def error(self, exception: Optional[type[Exception]] = None) -> Callable:
        """
        Decorator to register a custom error handler for commands.

        :param exception: The specific exception type to handle.
        :type exception: Optional[Exception]

        :return: A decorator that registers the given coroutine as
            an error handler.
        :rtype: Callable
        """

        def wrapper(func: ErrorCallback) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError('The error handler must be a coroutine.')

            if exception:
                self._error_handlers[exception] = func
            else:
                self._on_error = func
            return func
        return wrapper

    def get_room(self, room_id: str) -> Room:
        """
        Retrieve a Room instance based on the room_id.

        :param room_id: The ID of the room to retrieve.
        :type room_id: str
        :return: An instance of the Room class.
        :rtype: Room
        """
        return Room(room_id=room_id, bot=self)

    def _auto_register_events(self) -> None:
        for attr in dir(self):
            if not attr.startswith("on_"):
                continue
            coro = getattr(self, attr, None)
            if asyncio.iscoroutinefunction(coro):
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
        for event_type, funcs in self._handlers.items():
            if isinstance(event, event_type):
                for func in funcs:
                    await func(room, event)

    async def _process_commands(self, room: MatrixRoom, event: Event) -> None:
        """Parse and execute commands"""
        ctx = await self._build_context(room, event)

        if ctx.command:
            for check in self.checks:
                if not await check(ctx):
                    raise CheckError(ctx.command, check)

            await ctx.command(ctx)

    async def _build_context(self, room: MatrixRoom, event: Event):
        """Builds the base context and extracts the command from the event"""
        ctx = Context(bot=self, room=room, event=event)

        if not self.prefix or not ctx.body.startswith(self.prefix):
            return ctx

        if parts := ctx.body[len(self.prefix):].split():
            cmd_name = parts[0]
            cmd = self.commands.get(cmd_name)

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
