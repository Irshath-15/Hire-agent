from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./db/hiring_agent.db"
engine = create_engine(DATABASE_URL, echo=False)

def create_db():
    SQLModel.metadata.create_all(engine)

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