from abc import ABC, abstractmethod
from dataclasses import dataclass
from markdown import markdown
from typing import Any


class BaseMessageContent(ABC):
    """Base class for outgoing message payloads."""

    msgtype: str

    @abstractmethod
    def build(self) -> dict[str, Any]:
        pass


@dataclass
class TextContent(BaseMessageContent):
    msgtype = "m.text"
    body: str

    def build(self) -> dict:
        return {"msgtype": self.msgtype, "body": self.body}


@dataclass
class MarkdownMessage(TextContent):
    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.body,
            "format": "org.matrix.custom.html",
            "formatted_body": markdown(self.body, extensions=["nl2br"]),
        }


@dataclass
class NoticeContent(TextContent):
    msgtype = "m.notice"


@dataclass
class ReplyContent(TextContent):
    reply_to_event_id: str

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.body,
            "m.relates_to": {"m.in_reply_to": {"event_id": self.reply_to_event_id}},
        }


@dataclass
class EditContent(TextContent):
    original_event_id: str

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": f"* {self.body}",
            "m.new_content": {
                "msgtype": "m.text",
                "body": self.body,
            },
            "m.relates_to": {
                "rel_type": "m.replace",
                "event_id": self.original_event_id,
            },
        }


@dataclass
class FileContent(BaseMessageContent):
    msgtype = "m.file"
    filename: str
    url: str
    mimetype: str

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.filename,
            "url": self.url,
            "info": {"mimetype": self.mimetype},
        }


@dataclass
class ImageContent(BaseMessageContent):
    msgtype = "m.image"
    filename: str
    url: str
    mimetype: str
    height: int = 0
    width: int = 0

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.filename,
            "url": self.url,
            "info": {
                "mimetype": self.mimetype,
                "h": self.height,
                "w": self.width,
            },
        }


@dataclass
class AudioContent(BaseMessageContent):
    msgtype = "m.audio"
    filename: str
    url: str
    mimetype: str
    duration: int = 0

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.filename,
            "url": self.url,
            "info": {
                "mimetype": self.mimetype,
                "duration": self.duration,
            },
        }


@dataclass
class VideoContent(BaseMessageContent):
    msgtype = "m.video"
    filename: str
    url: str
    mimetype: str
    height: int = 0
    width: int = 0
    duration: int = 0

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.filename,
            "url": self.url,
            "info": {
                "mimetype": self.mimetype,
                "h": self.height,
                "w": self.width,
                "duration": self.duration,
            },
        }


@dataclass
class LocationContent(BaseMessageContent):
    msgtype = "m.location"
    geo_uri: str
    description: str = ""

    def build(self) -> dict:
        return {
            "msgtype": self.msgtype,
            "body": self.description or self.geo_uri,
            "geo_uri": self.geo_uri,
        }


@dataclass
class ReactionContent(BaseMessageContent):
    """For sending reactions to an event."""

    event_id: str
    emoji: str

    def build(self) -> dict:
        return {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": self.event_id,
                "key": self.emoji,
            }
        }
