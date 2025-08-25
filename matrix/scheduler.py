from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Any, Callable, Coroutine

Callback = Callable[..., Coroutine[Any, Any, Any]]


class Task:
    def __init__(self, cron: str, func: Callback) -> None:
        self.cron = cron
        self.func = func

    def _parse_cron(self) -> dict:
        """Parse a cron string into its components.

        :return: A dictionary with cron components.
        :rtype: dict
        """
        fields = self.cron.split()
        if len(fields) != 5:
            raise ValueError("Cron string must have exactly 5 fields")

        return {
            "minute": fields[0],
            "hour": fields[1],
            "day": fields[2],
            "month": fields[3],
            "day_of_week": fields[4],
        }


class Scheduler:
    def __init__(self) -> None:
        """The Scheduler class used to schedule tasks for a bot.

        Uses APScheduler under the hood.
        """
        self.scheduler = AsyncIOScheduler()
        self.tasks: list[Task] = []

    def schedule(self, cron: str, func: Callback) -> None:
        """
        Schedule a coroutine function to be run at specified intervals.

        :param cron: The cron string defining the schedule.
        :type cron: str
        :param func: The coroutine function to run.
        :type func: Callback
        """
        task = Task(cron, func)
        self.tasks.append(task)

        cron_trigger = CronTrigger(**task._parse_cron())
        self.scheduler.add_job(task.func, cron_trigger)

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()