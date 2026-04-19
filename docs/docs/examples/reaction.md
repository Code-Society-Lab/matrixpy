# Reactions

Demonstrates event listeners and the [`Message.react()`](../reference/message.md) API. The bot watches for incoming messages and reactions, and responds with emoji reactions of its own.

```python
--8<-- "examples/reaction.py"
```

Two event handlers are registered here:

- `on_message` — fires on every `RoomMessageText` event. It fetches the full message object and reacts based on the message body.
- `on_react` — fires on every `ReactionEvent`. It fetches the original message that was reacted to and chains a follow-up reaction.

`room.fetch_message()` returns a [`Message`](../reference/message.md) object. You can react with an emoji string or any short text.
