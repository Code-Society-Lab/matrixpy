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
        message: str = "",
        markdown: Optional[bool] = True,
        event: Optional[Event] = None,
        key: Optional[str] = None,
    ) -> None:
        """
        Send a message to the room.

        :param message: The message to send.
        :type message: str
        :param markdown: Whether to format the message as Markdown.
        :type markdown: Optional[bool]
        :param event: An event object to react to.
        :type event: Optional[Event]
        :param key: The reaction to the message.
        :type key: Optional[str]

        :raises MatrixError: If sending the message fails.
        """
        try:
            msg = Message(self.bot)
            if key:
                await msg.send_reaction(self.room_id, event, key)
            else:
                await msg.send(self.room_id, message, markdown)
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
            await self.bot.client.room_invite(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to invite user: {e}")

    async def ban_user(self, user_id: str, reason: Optional[str] = None) -> None:
        """
        Ban a user from a room.

        :param user_id: The ID of the user to ban of the room.
        :type user_id: str
        :param reason: The reason to ban the user.
        :type reason: Optional[str]

        :raises MatrixError: If banning the user fails.
        """
        try:
            # TODO: Abstract this to Context?
            await self.bot.client.room_ban(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to ban user: {e}")

    async def unban_user(self, user_id: str) -> None:
        """
        Unban a user from a room.

        :param user_id: The ID of the user to unban of the room.
        :type user_id: str

        :raises MatrixError: If unbanning the user fails.
        """
        try:
            # TODO: Abstract this to Context?
            await self.bot.client.room_unban(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to unban user: {e}")

    async def kick_user(self, user_id: str, reason: Optional[str] = None) -> None:
        """
        Kick a user from a room.

        :param user_id: The ID of the user to kick of the room.
        :type user_id: str
        :param reason: The reason to kick the user.
        :type reason: Optional[str]

        :raises MatrixError: If kicking the user fails.
        """
        try:
            # TODO: Abstract this to Context?
            await self.bot.client.room_kick(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to kick user: {e}")
