from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Job


# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request schema
class JobCreate(BaseModel):
    job_type: str = Field(min_length=1, max_length=100)
    payload: dict
    max_retries: int = Field(default=3, ge=0, le=10)


# Response schema
class JobResponse(BaseModel):
    id: int
    job_type: str
    payload: dict
    status: str
    attempts: int
    max_retries: int

    model_config = {"from_attributes": True}


app = FastAPI(
    title="Fault-Tolerant Distributed Job Queue by Thai Nguyen",
    version="0.1.0",
)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    job = Job(
        job_type=job_data.job_type,
        payload=job_data.payload,
        max_retries=job_data.max_retries,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    statement = select(Job)

    if status is not None:
        statement = statement.where(Job.status == status)

    statement = (
        statement
        .order_by(Job.created_at.desc(), Job.id.desc())
        .limit(limit)
    )

    return db.scalars(statement).all()


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job