from matrix.errors import MatrixError
from matrix.message import Message
from typing import TYPE_CHECKING, Optional
from nio import Event

if TYPE_CHECKING:
    from matrix.bot import Bot  # pragma: no cover


class Room:
    """
    Represents a Matrix room and provides methods to interact with it.

    :param room_id: The unique identifier of the room.
    :type room_id: str
    :param bot: The bot instance used to send messages.
    :type bot: Bot
    """

    def __init__(self, room_id: str, bot: "Bot") -> None:
        self.room_id = room_id
        self.bot = bot

    async def send(
        self,
        message: Optional[str] = None,
        markdown: Optional[bool] = True,
        event: Optional[Event] = None,
        key: Optional[str] = None,
    ) -> None:
        """
        Send a message to the room.

        :param message: The message to send.
        :type message: Optional[str]
        :param markdown: Whether to format the message as Markdown.
        :type markdown: Optional[bool]
        :param event: An event object to react to.
        :type event: Optional[Event]
        :param key: The reaction to the message.
        :type key: Optional[str]

        :raises MatrixError: If sending the message fails.
        """
        try:
            room = Message(self.bot)
            if key:
                await room.send_reaction(self.room_id, event, key)
            else:
                await room.send(self.room_id, message, markdown)
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    async def invite_user(self, user_id: str) -> None:
        """
        Invite a user to the room.

        :param user_id: The ID of the user to invite.
        :raises MatrixError: If inviting the user fails.
        """
        try:
            # TODO: Abstract this to Context?
            #       EX: await Context.invite_user_to_room(user_id)
            await self.bot.client.room_invite(
                room_id=self.room_id,
                user_id=user_id
            )
        except Exception as e:
            raise MatrixError(f"Failed to invite user: {e}")
