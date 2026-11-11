import pytest
from unittest.mock import MagicMock, AsyncMock

from matrix.scheduler import Scheduler


@pytest.fixture
def scheduler():
    s = Scheduler()
    # Mock the underlying APScheduler to avoid real scheduling
    s.scheduler = MagicMock()
    s.scheduler.get_jobs.return_value = []
    s.scheduler.add_job = MagicMock()
    s.scheduler.remove_job = MagicMock()
    return s


def test_unschedule_removes_job_by_name(scheduler):
    mock_job = MagicMock()
    mock_job.name = "morning_update"
    mock_job.id = "job123"
    scheduler.scheduler.get_jobs.return_value = [mock_job]

    scheduler.unschedule("morning_update")

    scheduler.scheduler.remove_job.assert_called_once_with("job123")


def test_unschedule_does_nothing_if_not_found(scheduler):
    mock_job = MagicMock()
    mock_job.name = "other_job"
    mock_job.id = "job456"
    scheduler.scheduler.get_jobs.return_value = [mock_job]

    scheduler.unschedule("morning_update")

    scheduler.scheduler.remove_job.assert_not_called()


def test_unschedule_handles_multiple_jobs(scheduler):
    job1 = MagicMock()
    job1.name = "job1"
    job1.id = "id1"
    job2 = MagicMock()
    job2.name = "morning_update"
    job2.id = "id2"
    scheduler.scheduler.get_jobs.return_value = [job1, job2]

    scheduler.unschedule("morning_update")

    scheduler.scheduler.remove_job.assert_called_once_with("id2")
