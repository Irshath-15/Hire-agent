from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool
import os

# Database path - use current directory (writable on Streamlit Cloud)
db_dir = os.path.expanduser("~/.streamlit_cache")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'hiring_agent.db')

DATABASE_URL = f"sqlite:///{db_path}"

# For SQLite: use StaticPool to avoid connection pool issues with Streamlit
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"check_same_thread": False, "timeout": 30},
    poolclass=StaticPool
)

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