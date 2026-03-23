import os
import sys
from sqlmodel import Session, select
from db.database import engine, create_db
from db.models import Candidate, JobDescription, Decision
from agent.parser import parse_resume
from agent.scorer import score_candidate, draft_rejection_email, draft_interview_email
from dotenv import load_dotenv

load_dotenv()

def process_resume(file_path: str, job_id: int) -> dict:
    create_db()

    with Session(engine) as session:
        job = session.get(JobDescription, job_id)
        if not job:
            raise ValueError(f"Job ID {job_id} not found")

        print(f"Parsing resume: {file_path}")
        parsed = parse_resume(file_path)

        candidate = Candidate(
            name=parsed.get("name") or "Unknown",
            email=parsed.get("email") or "unknown@email.com",
            phone=parsed.get("phone"),
            current_role=parsed.get("current_role"),
            experience_years=parsed.get("experience_years"),
            skills=parsed.get("skills"),
            education=parsed.get("education"),
            red_flags=parsed.get("red_flags"),
            raw_text=parsed.get("raw_text"),
            status="pending"
        )
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        print(f"Scoring candidate: {candidate.name}")
        score = score_candidate(parsed, job.description)

        candidate.score = score.get("overall_score")
        candidate.skills_match = score.get("skills_match")
        candidate.experience_fit = score.get("experience_fit")
        candidate.strengths = score.get("strengths")
        candidate.weaknesses = score.get("weaknesses")
        candidate.status = score.get("decision", "REVIEW").upper()
        session.add(candidate)

        decision = Decision(
            candidate_id=candidate.id,
            original_decision=candidate.status,
            notes=score.get("decision_reason")
        )
        session.add(decision)
        session.commit()
        session.refresh(candidate)

        print(f"Decision: {candidate.status} (Score: {candidate.score})")

        result = {
            "candidate_id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "score": candidate.score,
            "skills_match": candidate.skills_match,
            "experience_fit": candidate.experience_fit,
            "strengths": candidate.strengths,
            "weaknesses": candidate.weaknesses,
            "status": candidate.status,
            "decision_reason": score.get("decision_reason"),
            "red_flags": candidate.red_flags
        }

        if candidate.status == "REJECT":
            result["rejection_email"] = draft_rejection_email(
                candidate.name, job.title
            )

        return result

def create_job(title: str, description: str) -> int:
    create_db()
    with Session(engine) as session:
        job = JobDescription(title=title, description=description)
        session.add(job)
        session.commit()
        session.refresh(job)
        print(f"Job created with ID: {job.id}")
        return job.id

def get_all_candidates() -> list:
    create_db()
    with Session(engine) as session:
        candidates = session.exec(select(Candidate)).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "current_role": c.current_role,
                "experience_years": c.experience_years,
                "skills": c.skills,
                "score": c.score,
                "skills_match": c.skills_match,
                "experience_fit": c.experience_fit,
                "strengths": c.strengths,
                "weaknesses": c.weaknesses,
                "status": c.status,
                "red_flags": c.red_flags,
                "uploaded_at": str(c.uploaded_at)
            }
            for c in candidates
        ]

def get_all_jobs() -> list:
    create_db()
    with Session(engine) as session:
        jobs = session.exec(select(JobDescription)).all()
        return [
            {"id": j.id, "title": j.title, "description": j.description}
            for j in jobs
        ]

def override_decision(candidate_id: int, new_decision: str, notes: str = ""):
    create_db()
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        old_status = candidate.status
        candidate.status = new_decision.upper()
        session.add(candidate)

        decision = Decision(
            candidate_id=candidate_id,
            original_decision=old_status,
            hr_override=new_decision.upper(),
            notes=notes
        )
        session.add(decision)
        session.commit()
        print(f"Override: {old_status} → {new_decision.upper()}")