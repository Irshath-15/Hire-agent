import sys
sys.path.append("M:\\Hire-agent")

from agent.scorer import score_candidate, draft_rejection_email
import json

sample_candidate = {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "current_role": "Software Engineer",
    "experience_years": 5,
    "skills": "Python, FastAPI, React, PostgreSQL, Docker, Git",
    "education": "B.Tech Computer Science — Anna University",
    "red_flags": None
}

job_description = """
We are looking for a Senior Python Backend Developer.
Requirements:
- 4+ years of Python experience
- Strong knowledge of FastAPI or Django
- Experience with PostgreSQL
- Familiarity with Docker and cloud deployments
- Good communication skills
"""

print("Testing scorer...")
result = score_candidate(sample_candidate, job_description)
print(json.dumps(result, indent=2))

print("\nTesting rejection email...")
email = draft_rejection_email("John Doe", "Senior Python Backend Developer")
print(email)