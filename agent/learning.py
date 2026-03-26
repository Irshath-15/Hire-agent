import json
from sqlmodel import Session
from db.database import engine
from db.models import Candidate, Decision, MemoryRecord
from datetime import datetime


def learning_loop(batch_size: int = 50) -> dict:
    """Stub learning loop: aggregate decision data, regenerate candidate insights, store to memory."""
    with Session(engine) as session:
        decisions = session.query(Decision).order_by(Decision.decided_at.desc()).limit(batch_size).all()
        if not decisions:
            return {'status': 'noop', 'message': 'No decisions to learn from yet'}

        summary = []
        for d in decisions:
            c = session.get(Candidate, d.candidate_id)
            if not c:
                continue
            summary.append({
                'candidate': c.name,
                'status': c.status,
                'score': c.score,
                'decision': d.original_decision,
                'override': d.hr_override,
                'updated': d.decided_at.isoformat()
            })

        # crude 'learning' by storing JSON summary in memory store
        memory = MemoryRecord(candidate_id=0, job_id=0, summary=json.dumps(summary), embedding='', source='learning_loop')
        session.add(memory)
        session.commit()
        session.refresh(memory)

        return {
            'status': 'done',
            'records_processed': len(decisions),
            'memory_id': memory.id,
            'created_at': memory.created_at.isoformat()
        }


def get_learning_status() -> str:
    return f"Last learning run: {datetime.utcnow().isoformat()}"