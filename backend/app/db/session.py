import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# making this comment to test new deployment and check if CI still works
engine = create_engine(DATABASE_URL, future=True) if DATABASE_URL else None

SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
    if engine is not None
    else None
)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set in your environment.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()