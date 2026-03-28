import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def score_candidate(candidate: dict, job_description: str) -> dict:
    prompt = f"""You are an expert HR recruiter. Score this candidate against the job description and return ONLY a JSON object with no markdown or explanation.

{{
  "overall_score": "number between 0 and 100",
  "skills_match": "number between 0 and 100",
  "experience_fit": "number between 0 and 100",
  "strengths": "2-3 key strengths as a string",
  "weaknesses": "2-3 key weaknesses or gaps as a string",
  "decision": "SHORTLIST or REVIEW or REJECT",
  "decision_reason": "one sentence explaining the decision"
}}

Scoring rules:
- Overall score 70 and above → SHORTLIST
- Overall score 50 to 69 → REVIEW
- Overall score below 50 → REJECT

Job Description:
{job_description}

Candidate Profile:
- Name: {candidate.get('name')}
- Current Role: {candidate.get('current_role')}
- Experience: {candidate.get('experience_years')} years
- Skills: {candidate.get('skills')}
- Education: {candidate.get('education')}
- Red Flags: {candidate.get('red_flags')}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(clean)
        result["overall_score"] = float(result.get("overall_score", 0))
        result["skills_match"] = float(result.get("skills_match", 0))
        result["experience_fit"] = float(result.get("experience_fit", 0))
        return result
    except json.JSONDecodeError:
        return {
            "overall_score": 0,
            "skills_match": 0,
            "experience_fit": 0,
            "strengths": "Could not evaluate",
            "weaknesses": "Could not evaluate",
            "decision": "REVIEW",
            "decision_reason": "Scoring failed, needs manual review"
        }

def draft_rejection_email(candidate_name: str, job_title: str) -> str:
    """Generate a professional rejection email."""
    email_body = f"""Subject: Update on Your Application for {job_title}

Dear {candidate_name},

Thank you for submitting your application for the {job_title} position.

After careful consideration, we regret to inform you that you have not been selected for this role at this time.

We appreciate the time and effort you invested in your application and encourage you to apply for future openings.

Wishing you the very best in your career endeavors.

Best regards,
HireIQ Recruitment Team"""
    
    return email_body

def draft_interview_email(candidate_name: str, job_title: str,
                           interview_date: str, interview_time: str,
                           meet_link: str) -> str:
    """Generate a professional interview invitation email."""
    email_body = f"""Subject: Interview Invitation – {job_title}

Dear {candidate_name},

Congratulations! Your application for the {job_title} position has been shortlisted.

Your interview has been scheduled as follows:
- Date: {interview_date}
- Time: {interview_time}
- Mode / Venue: {meet_link}

Please confirm your availability by accepting the calendar invite. If you are unable to attend, please reach out to us to discuss alternate slots.

We look forward to speaking with you.

Best regards,
HireIQ Recruitment Team"""

    return email_body