import json
from sqlmodel import Session
from db.database import engine
from db.models import Candidate, Decision, MemoryRecord
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


def learning_loop(batch_size: int = 50) -> dict:
    """Enhanced learning loop: update ranking weights, compute Precision@N, store insights."""
    with Session(engine) as session:
        # Get recent decisions
        recent_date = datetime.utcnow() - timedelta(days=1)
        decisions = session.query(Decision).filter(Decision.decided_at >= recent_date).all()

        if not decisions:
            return {'status': 'noop', 'message': 'No recent decisions to learn from'}

        # Analyze decision patterns
        weights = update_ranking_weights(decisions, session)
        precision_metrics = compute_precision_at_n(decisions, session)

        # Store learning insights
        insights = {
            'weights_updated': weights,
            'precision_metrics': precision_metrics,
            'decisions_analyzed': len(decisions),
            'timestamp': datetime.utcnow().isoformat()
        }

        memory = MemoryRecord(
            candidate_id=0,
            job_id=0,
            summary=json.dumps(insights),
            embedding='',
            source='learning_loop'
        )
        session.add(memory)
        session.commit()
        session.refresh(memory)

        return {
            'status': 'done',
            'records_processed': len(decisions),
            'memory_id': memory.id,
            'weights': weights,
            'precision': precision_metrics,
            'created_at': memory.created_at.isoformat()
        }


def update_ranking_weights(decisions, session) -> dict:
    """Update ranking weights based on decision outcomes."""
    weights = defaultdict(float)
    total_decisions = len(decisions)

    for decision in decisions:
        candidate = session.get(Candidate, decision.candidate_id)
        if not candidate:
            continue

        # Analyze what factors led to the decision
        final_decision = decision.hr_override or decision.original_decision

        if final_decision == 'SHORTLIST':
            # Increase weights for factors that led to shortlisting
            weights['semantic_similarity'] += candidate.skills_match or 0
            weights['skills_match'] += candidate.skills_match or 0
            weights['experience_fit'] += candidate.experience_fit or 0
        elif final_decision == 'REJECT':
            # Decrease weights for factors that led to rejection
            weights['semantic_similarity'] -= (100 - (candidate.skills_match or 0)) / 100
            weights['skills_match'] -= (100 - (candidate.skills_match or 0)) / 100
            weights['experience_fit'] -= (100 - (candidate.experience_fit or 0)) / 100

    # Normalize weights
    if total_decisions > 0:
        for key in weights:
            weights[key] /= total_decisions

    return dict(weights)


def compute_precision_at_n(decisions, session, n_values=[1, 3, 5, 10]) -> dict:
    """Compute Precision@N metrics."""
    metrics = {}

    for n in n_values:
        # Get top N candidates by score
        candidates = session.query(Candidate).order_by(Candidate.score.desc()).limit(n).all()

        if not candidates:
            metrics[f'precision@{n}'] = 0.0
            continue

        # Count how many were actually shortlisted
        shortlisted_count = sum(1 for c in candidates if c.status == 'SHORTLIST')
        precision = shortlisted_count / len(candidates)
        metrics[f'precision@{n}'] = round(precision, 3)

    # Overall precision
    all_shortlisted = session.query(Candidate).filter(Candidate.status == 'SHORTLIST').count()
    all_candidates = session.query(Candidate).count()
    if all_candidates > 0:
        metrics['overall_precision'] = round(all_shortlisted / all_candidates, 3)

    return metrics


def get_learning_status() -> str:
    return f"Last learning run: {datetime.utcnow().isoformat()}"