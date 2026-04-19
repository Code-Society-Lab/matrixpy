# Scheduler

Shows how to run tasks on a cron schedule using `@bot.schedule`. Tasks run independently of commands — they fire at the specified time whether or not anyone sends a message.

```python
--8<-- "examples/scheduler.py"
```

`@bot.schedule` accepts a standard 5-field cron expression:

| Expression | Meaning |
|---|---|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour (on the hour) |
| `0 9 * * 1-5` | 9 AM every weekday |

The scheduled function receives no arguments. To send a message you need a [`Room`](../reference/room.md) object — get one with `bot.get_room(room_id)` before the bot starts, then call `room.send()` inside the task.

See the [`Scheduler` reference](../reference/scheduler.md) for the full API.
