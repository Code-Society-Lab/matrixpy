from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Any, Callable, Coroutine

Callback = Callable[..., Coroutine[Any, Any, Any]]


class Scheduler:
    def __init__(self) -> None:
        """The Scheduler class used to schedule tasks for a bot.

        Uses APScheduler under the hood.
        """
        self.scheduler = AsyncIOScheduler()

    def _parse_cron(self, cron: str) -> dict:
        """
        Parse a cron string into a dictionary suitable for CronTrigger.

        :param cron: The cron string to parse.
        :type cron: str
        :return: A dictionary with cron fields.
        :rtype: dict
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

        :param cron: The cron string defining the schedule.
        :type cron: str
        :param func: The coroutine function to run.
        :type func: Callback
        """
        cron_trigger = CronTrigger(**self._parse_cron(cron))
        self.scheduler.add_job(func, trigger=cron_trigger)

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()