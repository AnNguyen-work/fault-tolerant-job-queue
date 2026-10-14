from sqlalchemy import text
from app.database import engine


def main():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar_one()

            print(f"Database connection successful! Result: {value}")

    except Exception as error:
        print("Database connection failed.")
        print(f"Error: {error}")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()