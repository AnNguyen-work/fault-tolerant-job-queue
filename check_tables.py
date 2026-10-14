from sqlalchemy import inspect
from app.database import engine


inspector = inspect(engine)
tables = inspector.get_table_names()

print("Tables:", tables)

assert "jobs" in tables, "Jobs table was not created!"

print("Jobs table exists!")
engine.dispose()