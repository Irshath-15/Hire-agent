from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

DATABASE_URL = "sqlite:///./db/hiring_agent.db"
engine = create_engine(DATABASE_URL, echo=False)

def create_db():
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