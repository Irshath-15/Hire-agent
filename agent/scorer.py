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
    prompt = f"""Write a short, polite and professional rejection email for a job applicant.

Candidate name: {candidate_name}
Job title: {job_title}

Keep it warm, under 100 words, no placeholder brackets, ready to send as-is."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

def draft_interview_email(candidate_name: str, job_title: str,
                           interview_date: str, interview_time: str,
                           meet_link: str) -> str:
    prompt = f"""Write a short, professional interview confirmation email.

Candidate name: {candidate_name}
Job title: {job_title}
Interview date: {interview_date}
Interview time: {interview_time}
Google Meet link: {meet_link}

Keep it friendly, under 120 words, no placeholder brackets, ready to send as-is."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()