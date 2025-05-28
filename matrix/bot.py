import time
import asyncio
import logging
from collections import defaultdict
from typing import (
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from nio import (
    AsyncClient,
    Event,
    MatrixRoom,
    RoomMessageText,
    RoomMemberEvent,
    TypingNoticeEvent,
)

from matrix.context import Context

Callback = Callable[[Context], Awaitable[None]]

class Bot:
    EVENT_MAP: Dict[str, Type[Event]] = {
        "on_message":      RoomMessageText,
        "on_typing":       TypingNoticeEvent,
        "on_member_join":  RoomMemberEvent,
        "on_member_leave": RoomMemberEvent,
        "on_member_invite": RoomMemberEvent,
        "on_member_ban":    RoomMemberEvent,
        "on_member_kick":   RoomMemberEvent,
        "on_member_change": RoomMemberEvent,
    }

    def __init__(self, homeserver: str, *, prefix: str = "") -> None:
        self.client: AsyncClient = AsyncClient(homeserver)
        self.log: logging.Logger = logging.getLogger(__name__)

        self.prefix: str = prefix
        self.start_at: float | None = None  # unix timestamp

        self.commands: Dict[str, Callback] = {}
        self._handlers: Dict[Type[Event], List[Callback]] = defaultdict(list)

        self.client.add_event_callback(self._on_event, Event)
        self._auto_register_events()

    def event(
        self,
        func: Optional[Callback] = None,
        *,
        event_spec: Union[str, Type[Event], None] = None,
    ) -> Callable[[Callback], Callback]:
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
        name: str | None = None
    ) -> Callable[[Callback], Callback]:
        """
        Decorator to register a coroutine function as a command handler.

        The command name defaults to the function name unless
        explicitly provided.

        :param name: The name of the command. If omitted, the function name is used.
        :type name: str, optional
        :raises TypeError: If the decorated function is not a coroutine.
        :raises ValueError: If a command with the same name is registered.
        :return: Decorator that registers the command handler.
        :rtype: Callback
        """
        def wrapper(func: Callback) -> Callback:
            cmd_name = (name or func.__name__).lower()

            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Commands must be coroutines")

            if cmd_name in self.commands:
                raise ValueError(f"Command '{cmd_name}' already exists")

            self.commands[cmd_name] = func
            self.log.debug("registered command %s", cmd_name)

            return func
        return wrapper

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
            return True

        # ignore events that happened before the bot started
        if self.start_at and self.start_at > (event.server_timestamp / 1000):
            return True

        try:
            await self._dispatch(room, event)
        except Exception:
            self.log.exception(
                "uncaught exception while dispatching %s",
                event
            )

    async def _dispatch(self, room: MatrixRoom, event: Event) -> None:
        """Internal type-based fan-out plus optional command handling."""
        for event_type, funcs in self._handlers.items():
            if isinstance(event, event_type):
                for func in funcs:
                    try:
                        ctx = Context(bot=self, room=room, event=event)
                        await func(ctx)
                    except Exception:
                        self.log.exception(
                            "error in handler %s",
                            func.__name__
                        )

    async def _process_commands(
        self,
        ctx: Context
    ) -> None:
        """Parse and execute commands"""
        if not self.prefix or not ctx.event.body.startswith(self.prefix):
            return

        parts = ctx.event.body[len(self.prefix) :].split()
        if not parts:
            return

        cmd_name, *args = parts
        cmd = self.commands.get(cmd_name.lower())
        if not cmd:
            self.log.warning("unknown command '%s'", cmd_name)
            return

        try:
            await cmd(ctx)
        except Exception:
            self.log.exception("error while executing command '%s'", cmd_name)

    async def on_ready(self) -> None:  # noqa: D401 (keep name for consistency)
        """Invoked after a successful login, before sync starts."""
        self.log.info("bot is ready")

    async def on_message(self, ctx: Context):
        """
        Invoked when a message event is received.

        This method is automatically called when a :class:`nio.RoomMessageText`
        event is detected. It is primarily responsible for detecting and processing
        commands that match the bot's defined prefix.

        :param ctx: The context object containing information about the Matrix room and the message event.
        :type ctx: Context
        """
        await self._process_commands(ctx)

    async def run(self, user_id: str, password: str) -> None:
        """
        Log in to the Matrix homeserver and begin syncing events.

        This method should be used within an asynchronous context,
        typically via :func:`asyncio.run`. It handles authentication,
        calls the :meth:`on_ready` hook, and starts the long-running
        sync loop for receiving events.

        :param user_id: Fully-qualified Matrix user ID (e.g., ``@bot:example.org``).
        :type user_id: str
        :param password: Account password for the user.
        :type password: str
        """
        self.client.user = user_id

        self.start_at = time.time()
        self.log.info("starting – timestamp=%s", self.start_at)

        login_resp = await self.client.login(password)
        self.log.info("logged in: %s", login_resp)

        await self.on_ready()
        await self.client.sync_forever(timeout=30_000)

    def start(self, user_id: str, password: str) -> None:
        """
        Synchronous entry point for running the bot.

        This is a convenience wrapper that allows running the bot like a
        script using a blocking call. It internally calls :meth:`run` within
        :func:`asyncio.run`, and ensures the client is closed gracefully
        on interruption.

        :param user_id: Matrix user ID.
        :type user_id: str
        :param password: User password.
        :type password: str
        """
        try:
            asyncio.run(self.run(user_id, password))
        except KeyboardInterrupt:
            self.log.info("bot interrupted by user")
        finally:
            asyncio.run(self.client.close())
