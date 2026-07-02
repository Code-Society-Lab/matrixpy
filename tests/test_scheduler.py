import pytest
from matrixpy.scheduler import Scheduler

def test_list_jobs__expect_empty_list():
    """
    Verify list_jobs returns an empty list structure initially.
    """
    scheduler = Scheduler()
    assert scheduler.list_jobs() == []