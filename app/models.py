from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    job_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", index=True
    )

    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    locked_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    run_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc),
    index=True,
)

    last_error: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id}, "
            f"type={self.job_type!r}, "
            f"status={self.status!r})"
        )