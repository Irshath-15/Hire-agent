import os
import sys
import time
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from db.database import engine, create_db, save_memory_record, get_memory_records
from db.models import Candidate, JobDescription, Decision
from agent.parser import parse_resume
from agent.scorer import score_candidate, draft_rejection_email, draft_interview_email
from agent.semantic import similarity, embed_text
from agent.actions import send_email, schedule_interview, check_rsvp_responses, auto_reschedule, retry_email
from agent.learning import learning_loop
from dotenv import load_dotenv

load_dotenv()


def trigger_agent_on_upload(job_id: int, file_path: str) -> dict:
    """Entry point for HR upload trigger (Google Drive/Gmail/ATS Webhook)."""
    return run_hiring_pipeline(job_id, file_path)


def webhook_trigger(job_id: int, resume_urls: list, jd_url: str = None) -> dict:
    """Webhook trigger for external integrations (Google Drive, Gmail, ATS)."""
    # Download files from URLs if needed
    # For now, assume files are already downloaded to file_path
    # In production, implement download logic here
    results = []
    for resume_url in resume_urls:
        # Simulate processing each resume
        result = run_hiring_pipeline(job_id, resume_url)  # Assuming resume_url is local path
        results.append(result)
    return {'batch_processed': len(results), 'results': results}


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


def auto_reschedule_with_retry(candidate_email: str, job_title: str, interview_date: str, interview_time: str, max_retries: int = 3) -> dict:
    """Auto-reschedule interview with retry logic if candidate declines or no-shows."""
    for attempt in range(max_retries):
        reschedule_result = auto_reschedule(candidate_email, job_title, interview_date, interview_time)
        if reschedule_result.get('rescheduled'):
            # Send new invitation email
            new_date = reschedule_result['new_date']
            new_time = reschedule_result['new_time']
            email_body = draft_interview_email('Candidate', job_title, new_date, new_time, 'TBD')
            retry_email(candidate_email, f"Rescheduled Interview: {job_title}", email_body)
            return reschedule_result
        # Wait before checking again
        time.sleep(3600 * (attempt + 1))  # Wait 1, 2, 3 hours

    return {'rescheduled': False, 'reason': f'No response after {max_retries} checks'}


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

    try:
        print(f"\n[PIPELINE] Starting pipeline for {os.path.basename(file_path)} with job_id={job_id}")
        with Session(engine) as session:
            job = session.get(JobDescription, job_id)
            if not job:
                raise ValueError(f"Job ID {job_id} not found")

            # Step 1: Resume Parser + JD Embedding (Affinda/Unstructured + OpenAI Embeddings)
            print(f"[PIPELINE] Starting parse_resume...")
            parsed = parse_resume(file_path)
            print(f"[PIPELINE] Parsed result: {list(parsed.keys())}")
            
            jd_embedding = embed_text(job.description)  # Embed JD
            resume_embedding = embed_text(parsed.get('raw_text', ''))

            # Step 2: AI Brain (evaluate skills and experience)
            brain_data = ai_brain(parsed)

            # Step 3: Semantic Matching + Scoring
            semantic_data = semantic_match(job.description, parsed.get('raw_text', ''))
            score_data = score_and_reason(parsed, semantic_data, job.description)

            # Step 4: Decision Engine
            final_decision = decision_engine(score_data, parsed)

            # Create/update candidate record
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

            # Record decision
            decision = Decision(
                candidate_id=candidate.id,
                original_decision=final_decision,
                notes=score_data.get('decision_reason')
            )
            session.add(decision)
            session.commit()

            # Step 5: Email Automation + RSVP Handling
            action_results = action_engine(candidate, job, score_data)

            # Persist scheduling + email status into candidate record
            if action_results.get('schedule'):
                schedule_info = action_results['schedule']
                candidate.scheduled_at = datetime.utcnow()
                candidate.calendar_link = schedule_info.get('calendar_link')

            if action_results.get('email'):
                email_info = action_results['email']
                candidate.email_status = email_info.get('status')
                candidate.email_error = email_info.get('error') or email_info.get('message')

            session.add(candidate)
            session.commit()
            session.refresh(candidate)

            # If shortlisted, monitor RSVP and auto-reschedule if needed
            if candidate.status == 'SHORTLIST' and action_results.get('schedule'):
                schedule_info = action_results['schedule']
                # Check for RSVP responses and auto-reschedule
                reschedule_result = auto_reschedule_with_retry(
                    candidate.email, job.title,
                    schedule_info['interview_date'], schedule_info['interview_time']
                )
                if reschedule_result.get('rescheduled'):
                    # Update schedule info
                    action_results['schedule'].update(reschedule_result)
                    candidate.calendar_link = action_results['schedule'].get('calendar_link', candidate.calendar_link)
                    session.add(candidate)
                    session.commit()
                    session.refresh(candidate)

            # Step 6: Logging & Memory Store
            memory_summary = {
                'job': job.title,
                'candidate_name': candidate.name,
                'decision': final_decision,
                'score': score_data.get('overall_score'),
                'semantic_similarity': semantic_data.get('semantic_similarity'),
                'jd_embedding': jd_embedding,
                'resume_embedding': resume_embedding
            }

            try:
                memory_results = memory_store(
                    candidate.id,
                    job.id,
                    summary=str(memory_summary),
                    embedding=resume_embedding,
                    source='run_hiring_pipeline'
                )
            except Exception as e:
                print(f"Warning: Could not save memory: {e}")
                memory_results = {}

            # Step 7: Learning Loop (update weights nightly, compute Precision@N)
            learning_info = learning_loop()

            # Report generation
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
    except OperationalError as e:
        print(f"[PIPELINE] Database error: {e}")
        # Return a graceful error response
        return {
            'error': 'Database unavailable - data will be stored temporarily',
            'candidate_name': 'Unknown',
            'status': 'ERROR',
            'message': 'Resume processed but could not save to database. Please try again.'
        }
    except Exception as e:
        import traceback
        print(f"[PIPELINE] Unexpected error: {type(e).__name__}: {str(e)}")
        print(f"[PIPELINE] Traceback: {traceback.format_exc()}")
        return {
            'error': str(e),
            'status': 'ERROR',
            'message': f'Error processing resume: {str(e)}'
        }


def process_resume(file_path: str, job_id: int) -> dict:
    return run_hiring_pipeline(job_id, file_path)


def create_job(title: str, description: str) -> int:
    try:
        create_db()
        with Session(engine) as session:
            job = JobDescription(title=title, description=description)
            session.add(job)
            session.commit()
            session.refresh(job)
            print(f"Job created with ID: {job.id}")
            return job.id
    except Exception as e:
        print(f"Error creating job: {e}")
        raise


def get_all_candidates() -> list:
    try:
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
                    'scheduled_at': getattr(c, 'scheduled_at', None),
                    'calendar_link': getattr(c, 'calendar_link', None),
                    'email_status': getattr(c, 'email_status', None),
                    'email_error': getattr(c, 'email_error', None),
                    'uploaded_at': str(getattr(c, 'uploaded_at', ''))
                }
                for c in candidates
            ]
    except Exception as e:
        print(f"Warning: Could not fetch candidates: {e}")
        return []


def get_all_jobs() -> list:
    try:
        create_db()
        with Session(engine) as session:
            jobs = session.exec(select(JobDescription)).all()
            return [
                {'id': j.id, 'title': j.title, 'description': j.description}
                for j in jobs
            ]
    except Exception as e:
        print(f"Warning: Could not fetch jobs: {e}")
        return []


def override_decision(candidate_id: int, new_decision: str, notes: str = ''):
    try:
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
    except Exception as e:
        print(f"Error overriding decision: {e}")
        raise