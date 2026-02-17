import pytest
from unittest.mock import AsyncMock, Mock
from nio import MatrixRoom, RoomMessageText, AsyncClient
from matrix.errors import MatrixError
from matrix.context import Context
from matrix.room import Room
from matrix.message import Message


@pytest.fixture
def matrix_room():
    room = Mock(spec=MatrixRoom)
    room.room_id = "!room:example.com"
    room.name = "Test Room"
    room.display_name = "Test Room"
    room.topic = "A test room"
    room.member_count = 5
    room.encrypted = False
    return room


@pytest.fixture
def client():
    client = AsyncMock(spec=AsyncClient)
    return client


@pytest.fixture
def room(matrix_room, client):
    return Room(matrix_room, client)


@pytest.fixture
def bot(client):
    bot = Mock()
    bot.prefix = "!"
    bot.client = client
    bot.log = Mock()
    bot.log.getChild = Mock(return_value=Mock())
    return bot


@pytest.fixture
def event():
    return RoomMessageText.from_dict(
        {
            "content": {"body": "!echo hello world", "msgtype": "m.text"},
            "event_id": "$event123",
            "origin_server_ts": 123456,
            "sender": "@user:matrix.org",
            "type": "m.room.message",
        }
    )


@pytest.fixture
def context(bot, room, event):
    return Context(bot, room, event)


def test_context_initialization__expect_correct_properties(context, bot, room, event):
    assert context.bot is bot
    assert context.room is room
    assert context.event is event
    assert context.body == "!echo hello world"
    assert context.sender == "@user:matrix.org"
    assert context.prefix == "!"
    assert context.command is None
    assert context.subcommand is None
    assert context._args == ["!echo", "hello", "world"]


def test_args_without_command__expect_full_args_list(context):
    assert context.args == ["!echo", "hello", "world"]


def test_args_with_command__expect_args_without_command_name(context):
    context.command = Mock()
    assert context.args == ["hello", "world"]


def test_args_with_subcommand__expect_args_without_command_and_subcommand(context):
    context.command = Mock()
    context.subcommand = Mock()
    assert context.args == ["world"]


def test_logger_property__expect_room_specific_logger(context):
    logger = context.logger
    assert logger is not None
    context.bot.log.getChild.assert_called_once_with("!room:example.com")


@pytest.mark.asyncio
async def test_reply__expect_message_sent_to_room(context, client):
    mock_response = Mock()
    mock_response.event_id = "$reply123"
    client.room_send = AsyncMock(return_value=mock_response)

    msg = await context.reply("Hello!")

    client.room_send.assert_awaited_once()
    call_args = client.room_send.call_args
    assert call_args.kwargs["room_id"] == "!room:example.com"
    assert call_args.kwargs["message_type"] == "m.room.message"
    content = call_args.kwargs["content"]
    assert content["body"] == "Hello!"
    assert isinstance(msg, Message)


@pytest.mark.asyncio
async def test_reply_with_raw__expect_unformatted_message(context, client):
    mock_response = Mock()
    mock_response.event_id = "$reply123"
    client.room_send = AsyncMock(return_value=mock_response)

    await context.reply("Plain text", raw=True)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.text"
    assert content["body"] == "Plain text"
    assert "formatted_body" not in content


@pytest.mark.asyncio
async def test_reply_with_notice__expect_notice_message_type(context, client):
    mock_response = Mock()
    mock_response.event_id = "$reply123"
    client.room_send = AsyncMock(return_value=mock_response)

    await context.reply("Notice!", notice=True)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.notice"
    assert content["body"] == "Notice!"


@pytest.mark.asyncio
async def test_reply_with_file__expect_file_message_sent(context, client):
    from matrix.types import File

    mock_response = Mock()
    mock_response.event_id = "$reply123"
    client.room_send = AsyncMock(return_value=mock_response)

    file = File(
        filename="doc.pdf", path="mxc://example.com/abc", mimetype="application/pdf"
    )

    await context.reply(file=file)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.file"
    assert content["body"] == "doc.pdf"


@pytest.mark.asyncio
async def test_reply_with_image__expect_image_message_sent(context, client):
    from matrix.types import Image

    mock_response = Mock()
    mock_response.event_id = "$reply123"
    client.room_send = AsyncMock(return_value=mock_response)

    image = Image(
        filename="pic.jpg",
        path="mxc://example.com/xyz",
        mimetype="image/jpeg",
        width=800,
        height=600,
    )

    await context.reply(file=image)

    call_args = client.room_send.call_args
    content = call_args.kwargs["content"]
    assert content["msgtype"] == "m.image"
    assert content["body"] == "pic.jpg"


@pytest.mark.asyncio
async def test_reply_with_error__expect_matrix_error(context, client):
    client.room_send = AsyncMock(side_effect=Exception("Network failure"))

    with pytest.raises(MatrixError, match="Failed to send message"):
        await context.reply("This will fail")


@pytest.mark.asyncio
async def test_send_help_with_subcommand__expect_subcommand_help(context):
    context.subcommand = Mock()
    context.subcommand.help = "Subcommand help text"
    context.room.send = AsyncMock()

    await context.send_help()

    context.room.send.assert_awaited_once()
    call_args = context.room.send.call_args
    assert call_args.args[0] == "Subcommand help text"


@pytest.mark.asyncio
async def test_send_help_with_command__expect_command_help(context):
    context.command = Mock()
    context.command.help = "Command help text"
    context.room.send = AsyncMock()

    await context.send_help()

    context.room.send.assert_awaited_once()
    call_args = context.room.send.call_args
    assert call_args.args[0] == "Command help text"


@pytest.mark.asyncio
async def test_send_help_without_command__expect_bot_help_executed(context):
    context.bot.help = Mock()
    context.bot.help.execute = AsyncMock()

    await context.send_help()

    context.bot.help.execute.assert_awaited_once_with(context)
