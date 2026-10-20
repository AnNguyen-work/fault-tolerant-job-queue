import os
import time
import socket
import logging

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"

POLL_INTERVAL = 2
LEASE_SECONDS = 30
BASE_RETRY_DELAY = 5


def execute_job(job: Job) -> None:
    """Execute a job based on its type."""

    if job.job_type == "send_email":
        recipient = job.payload.get("recipient")
        subject = job.payload.get("subject")

        logger.info(
            "Simulating email to %s with subject %s",
            recipient,
            subject,
        )

        time.sleep(2)  

    elif job.job_type == "add_numbers":
        a = job.payload.get("a")
        b = job.payload.get("b")

        if not isinstance(a, (int, float)) or isinstance(a, bool):
            raise ValueError("'a' must be a number")

        if not isinstance(b, (int, float)) or isinstance(b, bool):
            raise ValueError("'b' must be a number")

        logger.info("Calculation result: %s", a + b)

    elif job.job_type == "test_failure":
        raise RuntimeError("Intentional failure for retry testing")

    else:
        raise ValueError(f"Unsupported job type: {job.job_type}")


def claim_job(db: Session):
    """Claim an available job or recover an expired lease."""

    now = datetime.now(timezone.utc)

    statement = (
        select(Job)
        .where(
            or_(
                (Job.status == "queued") & (Job.run_at <= now),
                (Job.status == "running") & (Job.locked_until < now),
            )
        )
        .order_by(Job.run_at, Job.created_at, Job.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    job = db.scalars(statement).first()

    if job is None:
        return None

    # Recover a previously running job whose lease expired.
    if job.status == "running":
        logger.warning("Recovering abandoned job %s", job.id)

    job.status = "running"
    job.locked_by = WORKER_ID
    job.locked_until = now + timedelta(seconds=LEASE_SECONDS)
    job.attempts += 1

    db.commit()

    logger.info(
        "Claimed job %s (attempt %s)",
        job.id,
        job.attempts,
    )

    return job.id



def process_job(job_id: int) -> None:
    """Execute a job and record its outcome."""

    started_at = time.perf_counter()

    with SessionLocal() as db:
        job = db.get(Job, job_id)

        if job is None:
            return

        # Avoid updating a job that another worker has reclaimed.
        if job.status != "running" or job.locked_by != WORKER_ID:
            logger.warning(
                "Job %s is no longer owned by worker %s",
                job_id,
                WORKER_ID,
            )
            return

        job_type = job.job_type
        outcome = "failed"

        try:
            execute_job(job)

            job.status = "completed"
            job.last_error = None
            outcome = "completed"

        except Exception as error:
            job.last_error = str(error)

            if job.attempts <= job.max_retries:
                delay = min(
                    BASE_RETRY_DELAY * (2 ** (job.attempts - 1)),
                    60,
                )

                job.status = "queued"
                job.run_at = datetime.now(timezone.utc) + timedelta(
                    seconds=delay
                )
                outcome = "retry_scheduled"

                logger.warning(
                    "Job %s failed on attempt %s. "
                    "Retry scheduled in %s seconds.",
                    job.id,
                    job.attempts,
                    delay,
                )

            else:
                job.status = "failed"

                logger.error(
                    "Job %s exhausted its retries.",
                    job.id,
                )

        finally:
            job.locked_by = None
            job.locked_until = None

        # Commit before reporting the final outcome.
        db.commit()

        duration_ms = (time.perf_counter() - started_at) * 1000

        logger.info(
            "Job processing finished: job_id=%s worker_id=%s "
            "job_type=%s outcome=%s duration_ms=%.2f",
            job_id,
            WORKER_ID,
            job_type,
            outcome,
            duration_ms,
        )


def run_worker():
    logger.info("Worker %s started", WORKER_ID)

    while True:
        try:
            with SessionLocal() as db:
                job_id = claim_job(db)

            if job_id is None:
                time.sleep(POLL_INTERVAL)
                continue

            process_job(job_id)

        except Exception:
            logger.exception("Worker encountered an error")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_worker()