
import pytest

from app.worker import execute_job


def test_add_numbers_success():
    from unittest.mock import Mock

    job = Mock()
    job.job_type = "add_numbers"
    job.payload = {"a": 10, "b": 20}

    # Should complete without raising an exception.
    execute_job(job)


def test_add_numbers_invalid_input():
    from unittest.mock import Mock

    job = Mock()
    job.job_type = "add_numbers"
    job.payload = {"a": "ten", "b": 20}

    with pytest.raises(ValueError, match="'a' must be a number"):
        execute_job(job)


def test_unsupported_job_type():
    from unittest.mock import Mock

    job = Mock()
    job.job_type = "unknown_job"
    job.payload = {}

    with pytest.raises(ValueError, match="Unsupported job type"):
        execute_job(job)


def test_test_failure_job():
    from unittest.mock import Mock

    job = Mock()
    job.job_type = "test_failure"
    job.payload = {}

    with pytest.raises(RuntimeError, match="Intentional failure"):
        execute_job(job)
