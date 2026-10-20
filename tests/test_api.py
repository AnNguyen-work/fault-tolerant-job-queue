
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "connected",
    }


def test_create_and_get_job():
    response = client.post(
        "/jobs",
        json={
            "job_type": "add_numbers",
            "payload": {"a": 10, "b": 20},
            "max_retries": 3,
        },
    )

    assert response.status_code == 201

    job = response.json()
    assert job["job_type"] == "add_numbers"
    assert job["status"] == "queued"
    assert job["attempts"] == 0

    job_id = job["id"]

    get_response = client.get(f"/jobs/{job_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == job_id


def test_get_nonexistent_job():
    response = client.get("/jobs/999999999")

    assert response.status_code == 404


def test_reject_invalid_max_retries():
    response = client.post(
        "/jobs",
        json={
            "job_type": "add_numbers",
            "payload": {"a": 10, "b": 20},
            "max_retries": 11,
        },
    )

    assert response.status_code == 422

def test_job_metrics():
    response = client.get("/metrics/jobs")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "by_status" in data

    expected_statuses = {
        "queued",
        "running",
        "completed",
        "failed",
    }

    assert set(data["by_status"].keys()) == expected_statuses

    assert all(
        isinstance(count, int) and count >= 0
        for count in data["by_status"].values()
    )

    assert data["total"] == sum(data["by_status"].values())
