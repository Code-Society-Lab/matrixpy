import pytest
from matrixpy.scheduler import Scheduler


def test_list_jobs_expect_empty() -> None:
    """Verify list_jobs returns an empty list on initialization."""
    scheduler = Scheduler()
    assert scheduler.list_jobs() == []


def test_list_jobs_with_active_jobs() -> None:
    """Verify list_jobs returns the names of the scheduled jobs."""
    scheduler = Scheduler()

    class MockJob:

        def __init__(self, name: str) -> None:
            self.name: str = name

    scheduler.jobs = [MockJob("job_1"), MockJob("job_2")]

    assert scheduler.list_jobs() == ["job_1", "job_2"]
