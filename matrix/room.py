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
    :param bot: The bot instance used to send messages.
    """

    def __init__(self, room_id: str, bot: "Bot") -> None:
        self.room_id = room_id
        self.bot = bot

    async def send(
        self,
        message: str = "",
        *,
        event: Event,
        markdown: Optional[bool] = True,
        key: Optional[str] = None,
    ) -> None:
        """
        Send a message to the room.

        :param message: The message to send.
        :param markdown: Whether to format the message as Markdown.
        :param event: An event object to react to.
        :param key: The reaction to the message.

        :raises MatrixError: If sending the message fails.
        """
        try:
            msg = self.get_message(self.bot, event)
            if key:
                await msg.send_reaction(self.room_id, key)
            else:
                await msg.send_message(self.room_id, message, markdown)
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    @staticmethod
    def get_message(bot: "Bot", event: Event) -> Message:
        """
        Get a Message instance from an event.
        :param bot: The bot instance to use for messages.
        :param event: The event object to construct the message from.

        :return: The constructed Message instance.
        """
        if not event and not bot:
            raise MatrixError("Failed to get message.")

        return Message.from_event(bot, event)

    async def react(self, event: Event, key: str) -> None:
        """
        Send a reaction to a message in the room.

        :param event: The event to react to.
        :param key: The reaction to the message.
        """
        try:
            await self.send(event=event, key=key)
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
        :param reason: The reason to ban the user.

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
        :param reason: The reason to kick the user.

        :raises MatrixError: If kicking the user fails.
        """
        try:
            # TODO: Abstract this to Context?
            await self.bot.client.room_kick(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to kick user: {e}")
