# Scheduler

`Scheduler` wraps APScheduler's `AsyncIOScheduler` to let you run recurring tasks inside a bot. Jobs are defined with standard cron expressions and are automatically started alongside the bot.

```python
from matrix import Bot

bot = Bot()

@bot.scheduler.job("0 9 * * 1-5")  # weekdays at 09:00
async def morning_standup():
    room = bot.get_room("!abc123:matrix.org")
    await room.send_text("Good morning, team! 🌅")
```

::: matrix.scheduler.Scheduler
