import pytest

from nio import RoomMessageText, RoomMemberEvent, TypingNoticeEvent, ReactionEvent

from matrix.registry import Registry
from matrix.command import Command
from matrix.group import Group
from matrix.errors import AlreadyRegisteredError


@pytest.fixture
def registry() -> Registry:
    return Registry(name="test", prefix="!")


async def _dummy(ctx):
    pass


async def _dummy_event(room, event):
    pass


async def _dummy_error(error):
    pass


async def _dummy_check(ctx):
    return True


def test_register_command_with_decorator__expect_command_in_registry(
    registry: Registry,
):
    @registry.command(description="A test command")
    async def ping(ctx):
        pass

    assert "ping" in registry.commands


def test_register_command_with_custom_name__expect_custom_name_in_registry(
    registry: Registry,
):
    @registry.command(name="pong")
    async def ping(ctx):
        pass

    assert "pong" in registry.commands
    assert "ping" not in registry.commands


def test_register_command_with_duplicate_name__expect_already_registered_error(
    registry: Registry,
):
    @registry.command()
    async def ping(ctx):
        pass

    with pytest.raises(AlreadyRegisteredError):

        @registry.command(name="ping")
        async def ping2(ctx):
            pass


def test_register_command_returns_command_instance__expect_command_type(
    registry: Registry,
):
    @registry.command()
    async def ping(ctx):
        pass

    assert isinstance(registry.commands["ping"], Command)


def test_register_command_directly_with_valid_command__expect_command_in_registry(
    registry: Registry,
):
    cmd = Command(_dummy, name="direct", prefix="!")
    registry.register_command(cmd)

    assert "direct" in registry.commands


def test_register_command_directly_with_duplicate__expect_already_registered_error(
    registry: Registry,
):
    cmd = Command(_dummy, name="dupe", prefix="!")
    registry.register_command(cmd)

    with pytest.raises(AlreadyRegisteredError):
        registry.register_command(cmd)


def test_register_group_with_decorator__expect_group_in_registry(registry: Registry):
    @registry.group(description="A test group")
    async def math(ctx):
        pass

    assert "math" in registry.commands


def test_register_group_with_custom_name__expect_custom_name_in_registry(
    registry: Registry,
):
    @registry.group(name="utils")
    async def utility(ctx):
        pass

    assert "utils" in registry.commands
    assert "utility" not in registry.commands


def test_register_group_with_duplicate_name__expect_already_registered_error(
    registry: Registry,
):
    @registry.group()
    async def math(ctx):
        pass

    with pytest.raises(AlreadyRegisteredError):

        @registry.group(name="math")
        async def math2(ctx):
            pass


def test_register_group_returns_group_instance__expect_group_type(registry: Registry):
    @registry.group()
    async def math(ctx):
        pass

    assert isinstance(registry.commands["math"], Group)


# ---------------------------------------------------------------------------
# event()
# ---------------------------------------------------------------------------


def test_register_event_by_function_name__expect_handler_registered(registry: Registry):
    @registry.event
    async def on_message(room, event):
        pass

    assert on_message in registry._event_handlers[RoomMessageText]


def test_register_event_with_string_spec__expect_handler_registered(registry: Registry):
    @registry.event(event_spec="on_typing")
    async def handle_typing(room, event):
        pass

    assert handle_typing in registry._event_handlers[TypingNoticeEvent]


def test_register_event_with_type_spec__expect_handler_registered(registry: Registry):
    @registry.event(event_spec=RoomMemberEvent)
    async def handle_member(room, event):
        pass

    assert handle_member in registry._event_handlers[RoomMemberEvent]


def test_register_event_with_unknown_name__expect_value_error(registry: Registry):
    with pytest.raises(ValueError):

        @registry.event
        async def on_unknown_event(room, event):
            pass


def test_register_event_with_unknown_string_spec__expect_value_error(
    registry: Registry,
):
    with pytest.raises(ValueError):

        @registry.event(event_spec="on_nonexistent")
        async def handler(room, event):
            pass


def test_register_event_with_non_coroutine__expect_type_error(registry: Registry):
    with pytest.raises(TypeError):

        @registry.event
        def on_message(room, event):  # not async
            pass


def test_register_multiple_handlers_for_same_event__expect_all_registered(
    registry: Registry,
):
    @registry.event
    async def on_message(room, event):
        pass

    @registry.event(event_spec="on_message")
    async def on_message_two(room, event):
        pass

    assert len(registry._event_handlers[RoomMessageText]) == 2


# ---------------------------------------------------------------------------
# register_event()
# ---------------------------------------------------------------------------


def test_register_event_directly_with_valid_handler__expect_handler_in_registry(
    registry: Registry,
):
    registry.register_event(ReactionEvent, _dummy_event)

    assert _dummy_event in registry._event_handlers[ReactionEvent]


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------


def test_register_check_with_coroutine__expect_check_in_list(registry: Registry):
    registry.check(_dummy_check)

    assert _dummy_check in registry._checks


def test_register_check_with_non_coroutine__expect_type_error(registry: Registry):
    def sync_check(ctx):
        return True

    with pytest.raises(TypeError):
        registry.check(sync_check)


def test_register_check_as_decorator__expect_check_in_list(registry: Registry):
    @registry.check
    async def only_admins(ctx):
        return True

    assert only_admins in registry._checks


def test_register_multiple_checks__expect_all_checks_in_list(registry: Registry):
    @registry.check
    async def check_one(ctx):
        return True

    @registry.check
    async def check_two(ctx):
        return True

    assert check_one in registry._checks
    assert check_two in registry._checks


def test_register_schedule_with_valid_cron__expect_job_in_scheduler(registry: Registry):
    @registry.schedule("0 9 * * *")
    async def morning_task():
        pass

    jobs = registry._scheduler.jobs
    assert any(j.func is morning_task for j in jobs)


def test_register_schedule_with_non_coroutine__expect_type_error(registry: Registry):
    with pytest.raises(TypeError):

        @registry.schedule("0 9 * * *")
        def not_async():
            pass


def test_register_multiple_schedules__expect_all_jobs_in_scheduler(registry: Registry):
    @registry.schedule("0 9 * * *")
    async def morning():
        pass

    @registry.schedule("0 18 * * *")
    async def evening():
        pass

    funcs = [j.func for j in registry._scheduler.jobs]
    assert morning in funcs
    assert evening in funcs


def test_register_error_handler_with_exception_type__expect_handler_in_dict(
    registry: Registry,
):
    @registry.error(ValueError)
    async def on_value_error(error):
        pass

    assert registry._error_handlers[ValueError] is on_value_error


def test_register_generic_error_handler__expect_fallback_error_handler_set(
    registry: Registry,
):
    @registry.error()
    async def on_any_error(error):
        pass

    assert registry._fallback_error_handler is on_any_error


def test_register_error_handler_with_non_coroutine__expect_type_error(
    registry: Registry,
):
    with pytest.raises(TypeError):

        @registry.error(ValueError)
        def sync_handler(error):
            pass


def test_register_multiple_typed_error_handlers__expect_all_in_dict(registry: Registry):
    @registry.error(ValueError)
    async def on_value_error(error):
        pass

    @registry.error(RuntimeError)
    async def on_runtime_error(error):
        pass

    assert ValueError in registry._error_handlers
    assert RuntimeError in registry._error_handlers


def test_register_error_handler_overwrites_previous_handler__expect_latest_handler(
    registry: Registry,
):
    @registry.error(ValueError)
    async def first_handler(error):
        pass

    @registry.error(ValueError)
    async def second_handler(error):
        pass

    assert registry._error_handlers[ValueError] is second_handler


def test_commands_property_with_empty_registry__expect_empty_dict(registry: Registry):
    assert registry.commands == {}


def test_commands_property_reflects_registered_commands__expect_correct_entries(
    registry: Registry,
):
    @registry.command()
    async def foo(ctx):
        pass

    @registry.group()
    async def bar(ctx):
        pass

    assert "foo" in registry.commands
    assert "bar" in registry.commands
    assert len(registry.commands) == 2
