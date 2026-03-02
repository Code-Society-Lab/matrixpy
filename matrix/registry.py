import inspect
import logging

from collections import defaultdict
from typing import Any, Callable, Coroutine, Optional, Type, Union, Dict, List

from nio import (
    Event,
    ReactionEvent,
    RoomMemberEvent,
    RoomMessageText,
    TypingNoticeEvent,
)

from matrix.group import Group
from matrix.command import Command
from matrix.scheduler import Scheduler
from matrix.errors import AlreadyRegisteredError

logger = logging.getLogger(__name__)

Callback = Callable[..., Coroutine[Any, Any, Any]]
GroupCallable = Callable[[Callable[..., Coroutine[Any, Any, Any]]], Group]
ErrorCallback = Callable[[Exception], Coroutine]
CommandErrorCallback = Callable[["Context", Exception], Coroutine[Any, Any, Any]]


class Registry:
    """
    Base class providing shared registration behaviour for Bot and Extension.

    Handles registration of commands, groups, events, checks, schedules,
    and error handlers. Subclasses must initialize the required attributes
    defined below, either directly or via ``super().__init__()``.
    """

    EVENT_MAP: dict[str, Type[Event]] = {
        "on_typing": TypingNoticeEvent,
        "on_message": RoomMessageText,
        "on_react": ReactionEvent,
        "on_member_join": RoomMemberEvent,
        "on_member_leave": RoomMemberEvent,
        "on_member_invite": RoomMemberEvent,
        "on_member_ban": RoomMemberEvent,
        "on_member_kick": RoomMemberEvent,
        "on_member_change": RoomMemberEvent,
    }

    def __init__(self, name: str, prefix: Optional[str] = None):
        self.name = name
        self.prefix = prefix
        self.log = logging.getLogger(__name__)

        self._commands: Dict[str, Command] = {}
        self._checks: List[Callback] = []
        self._scheduler: Scheduler = Scheduler()

        self._event_handlers: Dict[Type[Event], List[Callback]] = defaultdict(list)
        self._on_error: Optional[ErrorCallback] = None
        self._error_handlers: Dict[type[Exception], ErrorCallback] = {}
        self._command_error_handlers: Dict[type[Exception], CommandErrorCallback] = {}

    @property
    def commands(self) -> Dict[str, Command]:
        return self._commands

    def command(
        self,
        name: Optional[str] = None,
        *,
        description: Optional[str] = None,
        usage: Optional[str] = None,
        cooldown: Optional[tuple[int, float]] = None,
    ) -> Callable[[Callback], Command]:
        """Decorator to register a coroutine function as a command handler.

        The command name defaults to the function name unless
        explicitly provided.

        ## Example

        ```python
        @bot.command(description="Returns pong!")
        async def ping(ctx):
            await ctx.reply("Pong!")
        ```
        """
        def wrapper(func: Callback) -> Command:
            cmd = Command(
                func,
                name=name,
                description=description,
                prefix=self.prefix,
                usage=usage,
                cooldown=cooldown,
            )
            return self.register_command(cmd)
        return wrapper

    def register_command(self, cmd: Command) -> Command:
        """Register a Command instance directly.

        Prefer the :meth:`command` decorator for typical use. This method
        is useful when constructing a ``Command`` object manually or when
        loading commands from an extension.
        """
        if cmd.name in self._commands:
            raise AlreadyRegisteredError(cmd)

        self._commands[cmd.name] = cmd
        logger.debug("command '%s' registered on %s", cmd, type(self).__name__)

        return cmd

    def group(
        self,
        name: Optional[str] = None,
        *,
        description: Optional[str] = None,
        usage: Optional[str] = None,
        cooldown: Optional[tuple[int, float]] = None,
    ) -> Callable[[Callback], Group]:
        """Decorator to register a coroutine function as a command group.

        A group acts as a parent command that can have subcommands attached
        to it via its own ``@group.command()`` decorator. The group name
        defaults to the function name unless explicitly provided.

        ## Example

        ```python
        @bot.group(description="Group of mathematical commands")
        async def math(ctx):
            await ctx.reply("You called !math")

        @math.command()
        async def add(ctx, a: int, b: int):
            await ctx.reply(f"{a} + {b} = {a + b}")

        @math.command()
        async def subtract(ctx, a: int, b: int):
            await ctx.reply(f"{a} - {b} = {a - b}")
        ```
        """
        def wrapper(func: Callback) -> Group:
            grp = Group(
                func,
                name=name,
                description=description,
                prefix=self.prefix,
                usage=usage,
                cooldown=cooldown,
            )
            return self.register_group(grp)
        return wrapper

    def register_group(self, group: Group) -> Group:
        """Register a Group instance directly.

        Prefer the :meth:`group` decorator for typical use. This method
        is useful when constructing a ``Group`` object manually or when
        loading groups from an extension.
        """
        if group.name in self._commands:
            raise AlreadyRegisteredError(group)

        self._commands[group.name] = group
        logger.debug("group '%s' registered on %s", group, type(self).__name__)

        return group

    def event(
        self,
        func: Optional[Callback] = None,
        *,
        event_spec: Union[str, Type[Event], None] = None,
    ) -> Union[Callback, Callable[[Callback], Callback]]:
        """Decorator to register a coroutine as an event handler.

        Can be used with or without arguments. Without arguments, the event
        type is inferred from the function name via ``EVENT_MAP``. Multiple
        handlers for the same event type are supported and called in
        registration order.

        ## Example

        ```python
        @bot.event
        async def on_message(room, event):
            ...

        @bot.event(event_spec=RoomMemberEvent)
        async def handle_member(room, event):
            ...

        @bot.event(event_spec="on_member_join")
        async def welcome(room, event):
            ...
        ```
        """
        def wrapper(f: Callback) -> Callback:
            if not inspect.iscoroutinefunction(f):
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

            return self.register_event(event_type, f)

        if func is None:
            return wrapper
        return wrapper(func)

    def register_event(self, event_type: Type[Event], callback: Callback) -> Callback:
        """Register an event handler directly for a given event type.

        Prefer the :meth:`event` decorator for typical use. This method
        is useful when loading event handlers from an extension.
        """
        self._event_handlers[event_type].append(callback)
        logger.debug("registered event %s for %s", callback.__name__, event_type.__name__)
        return callback

    def check(self, func: Callback) -> Callback:
        """Register a global check that must pass before any command is invoked.

        The check receives the current :class:`Context` and must return a
        boolean. If any check returns ``False``, a :class:`CheckError` is
        raised and the command is not executed.

        ## Example

        ```python
        @bot.check
        async def is_not_banned(ctx):
            return ctx.sender not in banned_users
        ```
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Checks must be coroutines")

        self._checks.append(func)
        logger.debug("registered check '%s' on %s", func.__name__, type(self).__name__)

        return func

    def schedule(self, cron: str) -> Callable[[Callback], Callback]:
        """Decorator to register a coroutine as a scheduled task.

        When used on an extension, scheduled tasks are merged into the
        bot's scheduler when the extension is loaded.

        ## Example

        ```python
        @bot.schedule("0 9 * * *")
        async def morning_message():
            await room.send("Good morning!")
        ```
        """
        def wrapper(f: Callback) -> Callback:
            if not inspect.iscoroutinefunction(f):
                raise TypeError("Scheduled tasks must be coroutines")

            self._scheduler.schedule(cron, f)
            logger.debug("scheduled '%s' for cron '%s' on %s", f.__name__, cron, type(self).__name__)

            return f
        return wrapper

    def error(self, exception: Optional[type[Exception]] = None) -> Callable[[ErrorCallback], ErrorCallback]:
        """Decorator to register an error handler.

        If an exception type is provided, the handler is only invoked for
        that specific exception. If omitted, the handler acts as a generic
        fallback for any unhandled error.

        ## Example

        ```python
        @bot.error(ValueError)
        async def on_value_error(error):
            await room.send(f"Bad value: {error}")

        @bot.error()
        async def on_any_error(error):
            await room.send(f"Something went wrong: {error}")
        ```
        """
        def wrapper(func: ErrorCallback) -> ErrorCallback:
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Error handlers must be coroutines")

            if exception:
                self._error_handlers[exception] = func
            else:
                self._on_error = func
            logger.debug("registered error handler '%s' on %s", func.__name__, type(self).__name__)

            return func
        return wrapper