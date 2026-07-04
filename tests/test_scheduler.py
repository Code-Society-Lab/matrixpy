import pytest
from matrixpy.scheduler import Scheduler


def sample_task() -> None:
    pass


def test_scheduler_job_management() -> None:
    scheduler = Scheduler()
    
    # 1. Verify list_jobs returns an empty list on initialization
    assert scheduler.list_jobs() == []
    
    # 2. Verify list_jobs returns the correct name after scheduling
    scheduler.schedule("*/5 * * * *", sample_task)
    assert scheduler.list_jobs() == ["sample_task"]
    
    # 3. Verify unschedule cleanly removes the job from the system
    scheduler.unschedule("sample_task")
    assert scheduler.list_jobs() == []
