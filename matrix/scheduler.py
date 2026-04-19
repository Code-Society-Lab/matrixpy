from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
from typing import cast, Any, Callable, Coroutine

Callback = Callable[..., Coroutine[Any, Any, Any]]


class Scheduler:
    def __init__(self) -> None:
        """The Scheduler class used to schedule tasks for a bot.

        Uses APScheduler under the hood.
        """
        self.scheduler = AsyncIOScheduler()

    @property
    def jobs(self) -> list[Job]:
        return cast(list[Job], self.scheduler.get_jobs())

    def _parse_cron(self, cron: str) -> dict:
        """
        Parse a cron string into a dictionary suitable for CronTrigger.
        """
        fields = cron.split()
        if len(fields) != 5:
            raise ValueError("Cron string must have exactly 5 fields")
        return {
            "minute": fields[0],
            "hour": fields[1],
            "day": fields[2],
            "month": fields[3],
            "day_of_week": fields[4],
        }

    def schedule(self, cron: str, func: Callback) -> None:
        """
        Schedule a coroutine function to be run at specified intervals.

        ## Example

        ```python
        @bot.schedule("0 9 * * 1-5")
        async def morning_update() -> None:
            await room.send("Good morning!")
        ```
        """
        cron_trigger = CronTrigger(**self._parse_cron(cron))
        self.scheduler.add_job(func, trigger=cron_trigger, name=func.__name__)

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
