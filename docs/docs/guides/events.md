# What are Events?
In Matrix, [events](https://spec.matrix.org/latest/#events) are the fundamental building blocks of communication. Everything that happens in a Matrix room is represented as an event:
- Someone sends a message → `RoomMessageText` event
- Someone joins a room → `RoomMemberEvent` event
- Someone reacts to a message → `ReactionEvent` event
- Someone starts typing → `TypingNoticeEvent` event

### Events vs Commands: When to Use Which?
Use **events** for automatic reactions to room activity. Use **commands** for user-initiated actions.

| Scenario | Use Events | Use Commands |
|----------|------------|--------------|
| Welcome new members | ✅ Yes | ❌ No |
| Respond to `!ping` | ❌ No | ✅ Yes |
| Log all messages | ✅ Yes | ❌ No |
| Perform math calculation | ❌ No | ✅ Yes |
| React to room activity | ✅ Yes | ❌ No |
| Execute user requests | ❌ No | ✅ Yes |

### Available Events Quick Reference

| Event | Trigger |
|-------|---------|
| `on_message` | Text message sent |
| `on_typing` | Typing status changes |
| `on_react` | Reaction added to message |
| `on_member_join` | User joins room |
| `on_member_leave` | User leaves room |
| `on_member_invite` | User invited to room |
| `on_member_ban` | User banned from room |
| `on_member_kick` | User kicked from room |
| `on_member_change` | Member profile updated |

# Event Handler
An event handler is a function that runs automatically when a specific event occurs. It is defined with the `@bot.event` decorator (see [`Bot`](../reference/bot.md)):

```python
@bot.event
async def on_message(room, event):
    """This runs every time someone sends a message"""
    print(f"Message in {room.name}: {event.body}")
```

### Creating Event Handlers
#### Method 1: Automatic Registration (Recommended in most cases)
The simplest way is to name your function to match the event:

```python
@bot.event
async def on_message(room, event):
    """Function name matches the event"""
    print(f"Message: {event.body}")
```
Matrix.py automatically knows `on_message` should handle `RoomMessageText` events.

**Supported Names**:
- `on_message`
- `on_typing`
- `on_react`
- `on_member_join`
- `on_member_leave`
- `on_member_invite`
- `on_member_ban`
- `on_member_kick`
- `on_member_change`

#### Method 2: Using String Event Names
You can also use the string event name:

```python
@bot.event(event_spec="on_message")
async def log_all_messages(room, event):
    """Using string event name"""
    logging.info(f"Message logged: {event.body}")
```
This is useful when you want multiple handlers for the same event type.

#### Method 3: Explicit Event Type (More Flexible)
You can name your function anything and specify the event type:

```python
from nio import RoomMessageText


@bot.event(event_spec=RoomMessageText)
async def my_custom_message_handler(room, event):
    """Custom function name, explicit event type"""
    room.send(f"Message: {event.body}")
```

This is useful when you want:
- Custom function names
- Multiple handlers for the same event type
- To handle event types not in the convenience list


### Understanding the Parameters
Every event handler receives two parameters:

**1. `room` - The [`Room`](../reference/room.md) object**
- Contains information about the room where the event occurred
- Common attributes:
  - `room.room_id` - Unique room identifier (e.g., `"!abc123:example.com"`)
  - `room.name` - Human-readable room name (e.g., `"General Chat"`)
  - `room.display_name` - Display name of the room
  - `room.topic` - Room topic/description
  - `room.member_count` - Number of members in the room
- Allows you to interact with the room, for example send a message (`room.send("hello world")`) — see the [`Room`](../reference/room.md) reference for all available methods.

**2. `event` - The Event object**
- Contains information about what happened
- Attributes vary by event type, but common ones include:
  - `event.sender` - User who triggered the event (e.g., `"@alice:example.com"`)
  - `event.server_timestamp` - When the event occurred (milliseconds since epoch)
  - `event.event_id` - Unique identifier for this specific event
