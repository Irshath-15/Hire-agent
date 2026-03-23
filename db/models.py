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