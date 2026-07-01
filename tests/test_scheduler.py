import pytest
# Assuming Scheduler is imported from your main module package structure
# Adjust the import line below if the project structure uses a different path
from matrixpy.scheduler import Scheduler  

def test_list_jobs_empty():
    """Verify list_jobs returns an empty list or initialized structure initially."""
    scheduler = Scheduler()
    assert isinstance(scheduler.list_jobs(), list)

def test_list_jobs_content():
    """Verify list_jobs returns a list format properly."""
    scheduler = Scheduler()
    # If jobs are added during initialization or tests, verify it handles it gracefully
    jobs = scheduler.list_jobs()
    assert list(jobs) == jobs
