import pytest
from matrixpy.scheduler import Scheduler


def test_list_jobs__expect_empty():
    """Verify list_jobs returns an empty list or initialized structure."""
    scheduler = Scheduler()
    assert scheduler.list_jobs() == []
