
from sqlalchemy import text
from app.database import engine

with engine.begin() as conn:
    conn.execute(
        text("""
            ALTER TABLE jobs
            ADD COLUMN IF NOT EXISTS run_at
            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)
    )

print("Database updated successfully")