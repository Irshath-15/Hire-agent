from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import os

# Use a path that works better on Streamlit Cloud
# Streamlit Cloud: Use /tmp for ephemeral storage (will reset on redeployment)
# Local: Use ./db/ directory
if os.environ.get("STREAMLIT_SERVER_HEADLESS"):
    # Running on Streamlit Cloud
    db_path = "/tmp/hiring_agent.db"
else:
    # Running locally
    os.makedirs("db", exist_ok=True)
    db_path = "./db/hiring_agent.db"

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def create_db():
    try:
        SQLModel.metadata.create_all(engine)
        # Sqlalchemy create_all doesn't alter existing tables; ensure new columns exist after code changes.
        with engine.begin() as conn:
            for col_def in [
                "scheduled_at DATETIME",
                "calendar_link TEXT",
                "email_status TEXT",
                "email_error TEXT",
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE candidate ADD COLUMN {col_def}"))
                except OperationalError:
                    pass
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        # Continue anyway - database may be created on first use

def get_session():
    with Session(engine) as session:
        yield session


def save_memory_record(candidate_id: int, job_id: int, summary: str, embedding: str, source: str = "pipeline"):
    from db.models import MemoryRecord
    with Session(engine) as session:
        record = MemoryRecord(
            candidate_id=candidate_id,
            job_id=job_id,
            summary=summary,
            embedding=embedding,
            source=source
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_memory_records(candidate_id: int = None, job_id: int = None):
    from db.models import MemoryRecord
    from sqlmodel import select
    with Session(engine) as session:
        query = select(MemoryRecord)
        if candidate_id is not None:
            query = query.where(MemoryRecord.candidate_id == candidate_id)
        if job_id is not None:
            query = query.where(MemoryRecord.job_id == job_id)
        return session.exec(query).all()