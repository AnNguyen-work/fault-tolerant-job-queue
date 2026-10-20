
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_multiple_jobs_processed_by_workers():
    job_ids = []

    # Submit five independent jobs.
    for i in range(5):
        response = client.post(
            "/jobs",
            json={
                "job_type": "add_numbers",
                "payload": {"a": i, "b": 10},
                "max_retries": 3,
            },
        )

        assert response.status_code == 201
        job_ids.append(response.json()["id"])

    # Wait up to 30 seconds for all jobs to finish.
    deadline = time.time() + 30

    while time.time() < deadline:
        responses = [
            client.get(f"/jobs/{job_id}") for job_id in job_ids
        ]

        assert all(r.status_code == 200 for r in responses)

        jobs = [r.json() for r in responses]

        if all(job["status"] == "completed" for job in jobs):
            break

        time.sleep(1)

    assert all(job["status"] == "completed" for job in jobs)

    # Each job should have been claimed exactly once.
    assert all(job["attempts"] == 1 for job in jobs)
