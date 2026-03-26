import os
import tempfile
from db.database import create_db, engine
from db.models import Candidate, JobDescription, Decision, MemoryRecord
from sqlmodel import Session
import agent.pipeline as pipeline


def setup_function():
    create_db()
    with Session(engine) as session:
        session.query(Decision).delete()
        session.query(Candidate).delete()
        session.query(JobDescription).delete()
        session.query(MemoryRecord).delete()
        session.commit()


def test_decision_engine_flag_on_red_flags():
    score = {'decision': 'SHORTLIST'}
    parsed = {'red_flags': 'history gaps'}
    assert pipeline.decision_engine(score, parsed) == 'FLAG'


def test_semantic_match_similarity():
    job_description = 'Senior Python developer with FastAPI and Postgres experience.'
    resume_text = 'Python backend engineer with FastAPI, SQLAlchemy, Postgres and cloud deployment.'
    sem = pipeline.semantic_match(job_description, resume_text)
    assert 'semantic_similarity' in sem
    assert sem['semantic_similarity'] > 40


def test_run_hiring_pipeline_with_mocked_components(monkeypatch):
    # monkeypatch external resource calls
    monkeypatch.setattr(pipeline, 'parse_resume', lambda _: {
        'name': 'Jane Test',
        'email': 'jane.test@example.com',
        'phone': '+10000000000',
        'current_role': 'Backend Engineer',
        'experience_years': 6,
        'skills': 'Python, FastAPI, Postgres',
        'education': 'MS Computer Science',
        'red_flags': None,
        'raw_text': 'Resume text ...'
    })

    monkeypatch.setattr(pipeline, 'score_candidate', lambda parsed, jd: {
        'overall_score': 92,
        'skills_match': 90,
        'experience_fit': 85,
        'strengths': 'Strong Python and backend experience',
        'weaknesses': 'Limited frontend exposure',
        'decision': 'SHORTLIST',
        'decision_reason': 'Strong skill match.'
    })

    monkeypatch.setattr(pipeline, 'draft_interview_email', lambda name, title, date, time, link: 'Interview email body')
    monkeypatch.setattr(pipeline, 'draft_rejection_email', lambda name, title: 'Rejection email body')
    monkeypatch.setattr(pipeline, 'send_email', lambda to, subject, text: {'status': 'sent'})
    monkeypatch.setattr(pipeline, 'schedule_interview', lambda *args, **kwargs: {
        'interview_date': '2099-12-31', 'interview_time': '10:00 AM', 'calendar_link': 'https://example.com'
    })
    monkeypatch.setattr(pipeline, 'learning_loop', lambda: {'status': 'done', 'records_processed': 0})

    # setup test job and temporary resume file
    job_id = pipeline.create_job('Senior Role', 'Python and FastAPI required')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as fp:
        fp.write(b'Synthetic resume text')
        path = fp.name

    try:
        result = pipeline.run_hiring_pipeline(job_id, path)
        assert result['status'] == 'SHORTLIST'
        assert result['candidate_id'] is not None
        assert result['job_id'] == job_id
        assert result['action']['action'] == 'shortlist'

        # check memory record persisted
        memory_records = pipeline.get_memory_records(candidate_id=result['candidate_id'])
        assert len(memory_records) >= 1

    finally:
        os.remove(path)
