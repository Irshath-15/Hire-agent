from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    phone: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[float] = None
    education: Optional[str] = None
    current_role: Optional[str] = None
    raw_text: Optional[str] = None
    score: Optional[float] = None
    skills_match: Optional[float] = None
    experience_fit: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    red_flags: Optional[str] = None
    status: str = Field(default="pending")
    scheduled_at: Optional[datetime] = None
    calendar_link: Optional[str] = None
    email_status: Optional[str] = None
    email_error: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class JobDescription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Decision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int
    original_decision: str
    hr_override: Optional[str] = None
    notes: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int
    job_id: int
    summary: Optional[str] = None
    embedding: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)