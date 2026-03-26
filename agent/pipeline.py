import os
import sys
from sqlmodel import Session, select
from db.database import engine, create_db, save_memory_record, get_memory_records
from db.models import Candidate, JobDescription, Decision
from agent.parser import parse_resume
from agent.scorer import score_candidate, draft_rejection_email, draft_interview_email
from agent.semantic import similarity, embed_text
from agent.actions import send_email, schedule_interview
from agent.learning import learning_loop
from dotenv import load_dotenv

load_dotenv()


def trigger_agent_on_upload(job_id: int, file_path: str) -> dict:
    """Entry point for HR upload trigger."""
    return run_hiring_pipeline(job_id, file_path)


def ai_brain(parsed_resume: dict) -> dict:
    """Evaluate extracted skills and experience for additional metadata."""
    return {
        'skills': parsed_resume.get('skills'),
        'experience_years': parsed_resume.get('experience_years'),
        'red_flags': parsed_resume.get('red_flags')
    }


def semantic_match(job_description: str, resume_text: str) -> dict:
    score = similarity(job_description, resume_text)
    return {
        'semantic_similarity': round(score * 100, 2)
    }


def score_and_reason(parsed_resume: dict, semantic_data: dict, job_description: str) -> dict:
    candidate_score = score_candidate(parsed_resume, job_description)
    candidate_score['semantic_similarity'] = semantic_data.get('semantic_similarity', 0)
    if candidate_score['overall_score'] >= 90:
        candidate_score['decision'] = 'SHORTLIST'
        candidate_score['decision_reason'] = candidate_score.get('decision_reason', '') + ' High confidence from semantic match.'
    elif candidate_score['overall_score'] < 40 or parsed_resume.get('red_flags'):
        candidate_score['decision'] = 'REJECT'
        candidate_score['decision_reason'] = candidate_score.get('decision_reason', '') + ' Low score or red flags detected.'
    return candidate_score


def ranking_engine(limit: int = 10) -> list:
    create_db()
    with Session(engine) as session:
        candidates = session.exec(select(Candidate)).all()
        ranked = sorted(candidates, key=lambda c: (c.score or 0), reverse=True)
        return ranked[:limit]


def decision_engine(score_data: dict, parsed_resume: dict) -> str:
    decision = score_data.get('decision', 'REVIEW').upper()
    if parsed_resume.get('red_flags') and decision != 'REJECT':
        return 'FLAG'
    return decision


def action_engine(candidate: Candidate, job: JobDescription, score_data: dict) -> dict:
    result = {'action': None, 'email': None, 'schedule': None}

    if candidate.status == 'SHORTLIST':
        interview_info = schedule_interview(
            candidate.name, candidate.email, job.title
        )
        email_body = draft_interview_email(
            candidate.name, job.title,
            interview_info['interview_date'], interview_info['interview_time'],
            interview_info.get('calendar_link', 'TBD')
        )
        email_result = send_email(candidate.email, f"Interview Invitation: {job.title}", email_body)
        result.update({'action': 'shortlist', 'schedule': interview_info, 'email': email_result})

    elif candidate.status == 'REJECT':
        email_body = draft_rejection_email(candidate.name, job.title)
        email_result = send_email(candidate.email, f"Update on {job.title} application", email_body)
        result.update({'action': 'reject', 'email': email_result})

    elif candidate.status == 'FLAG':
        red_flags = score_data.get('red_flags') or candidate.red_flags or 'None'
        email_body = f"Candidate requires manual review due to red flags: {red_flags}"
        result.update({'action': 'flag', 'note': email_body})

    else:
        result.update({'action': 'review', 'note': 'Pending manual review'})

    return result


def dashboard_update(candidate: Candidate) -> dict:
    return {
        'candidate_id': candidate.id,
        'status': candidate.status,
        'score': candidate.score,
        'updated_at': str(candidate.uploaded_at)
    }


def memory_store(candidate_id: int, job_id: int, summary: str, embedding: str, source: str = 'pipeline') -> dict:
    record = save_memory_record(candidate_id, job_id, summary, embedding, source)
    return {
        'memory_id': record.id,
        'candidate_id': record.candidate_id,
        'job_id': record.job_id,
        'source': record.source
    }


def run_hiring_pipeline(job_id: int, file_path: str) -> dict:
    create_db()

    with Session(engine) as session:
        job = session.get(JobDescription, job_id)
        if not job:
            raise ValueError(f"Job ID {job_id} not found")

        parsed = parse_resume(file_path)
        brain_data = ai_brain(parsed)
        semantic_data = semantic_match(job.description, parsed.get('raw_text', ''))
        score_data = score_and_reason(parsed, semantic_data, job.description)
        final_decision = decision_engine(score_data, parsed)

        candidate = Candidate(
            name=parsed.get('name') or 'Unknown',
            email=parsed.get('email') or 'unknown@email.com',
            phone=parsed.get('phone'),
            current_role=parsed.get('current_role'),
            experience_years=parsed.get('experience_years'),
            skills=parsed.get('skills'),
            education=parsed.get('education'),
            red_flags=parsed.get('red_flags'),
            raw_text=parsed.get('raw_text'),
            score=score_data.get('overall_score', 0),
            skills_match=score_data.get('skills_match', 0),
            experience_fit=score_data.get('experience_fit', 0),
            strengths=score_data.get('strengths'),
            weaknesses=score_data.get('weaknesses'),
            status=final_decision
        )

        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        decision = Decision(
            candidate_id=candidate.id,
            original_decision=final_decision,
            notes=score_data.get('decision_reason')
        )
        session.add(decision)
        session.commit()

        action_results = action_engine(candidate, job, score_data)
        memory_summary = {
            'job': job.title,
            'candidate_name': candidate.name,
            'decision': final_decision,
            'score': score_data.get('overall_score'),
            'semantic_similarity': semantic_data.get('semantic_similarity')
        }

        memory_results = memory_store(
            candidate.id,
            job.id,
            summary=str(memory_summary),
            embedding=embed_text(parsed.get('raw_text', '')),
            source='run_hiring_pipeline'
        )

        learning_info = learning_loop()

        extracted_text = parsed.get('raw_text', '') or ''
        is_scanned_image = extracted_text.startswith('[Image resume:')

        report = {
            'source_file': file_path,
            'raw_text_length': len(extracted_text),
            'parsed_fields': {k: v for k, v in parsed.items() if k != 'raw_text'},
            'is_scanned_image': is_scanned_image,
            'scan_status': 'ocr_failed' if is_scanned_image else 'ok'
        }

        base = {
            'candidate_id': candidate.id,
            'name': candidate.name,
            'email': candidate.email,
            'status': candidate.status,
            'score': candidate.score,
            'skills_match': candidate.skills_match,
            'experience_fit': candidate.experience_fit,
            'strengths': candidate.strengths,
            'weaknesses': candidate.weaknesses,
            'red_flags': candidate.red_flags,
            'job_id': job.id,
            'job_title': job.title,
            'decision_reason': score_data.get('decision_reason'),
            'semantic_similarity': semantic_data.get('semantic_similarity'),
            'report': report
        }
        base.update({
            'analysis': score_data,
            'semantic': semantic_data,
            'action': action_results,
            'memory': memory_results,
            'learning': learning_info,
            'dashboard': dashboard_update(candidate)
        })
        return base


def process_resume(file_path: str, job_id: int) -> dict:
    return run_hiring_pipeline(job_id, file_path)


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
                'id': c.id,
                'name': getattr(c, 'name', None) or 'Unknown',
                'email': getattr(c, 'email', None) or 'N/A',
                'current_role': getattr(c, 'current_role', None),
                'experience_years': getattr(c, 'experience_years', None),
                'skills': getattr(c, 'skills', None),
                'education': getattr(c, 'education', None),
                'score': getattr(c, 'score', None),
                'skills_match': getattr(c, 'skills_match', None),
                'experience_fit': getattr(c, 'experience_fit', None),
                'strengths': getattr(c, 'strengths', None),
                'weaknesses': getattr(c, 'weaknesses', None),
                'status': getattr(c, 'status', 'PENDING'),
                'red_flags': getattr(c, 'red_flags', None),
                'uploaded_at': str(getattr(c, 'uploaded_at', ''))
            }
            for c in candidates
        ]


def get_all_jobs() -> list:
    create_db()
    with Session(engine) as session:
        jobs = session.exec(select(JobDescription)).all()
        return [
            {'id': j.id, 'title': j.title, 'description': j.description}
            for j in jobs
        ]


def override_decision(candidate_id: int, new_decision: str, notes: str = ''):
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