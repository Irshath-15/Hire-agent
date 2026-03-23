import sys
sys.path.append("M:\\Hire-agent")

from agent.pipeline import create_job, process_resume, get_all_candidates
from agent.parser import parse_resume_with_ai
from agent.scorer import score_candidate
import json

job_description = """
We are looking for a Senior Python Backend Developer.
Requirements:
- 4+ years of Python experience
- Strong knowledge of FastAPI or Django
- Experience with PostgreSQL
- Familiarity with Docker and cloud deployments
- Good communication skills
"""

print("Step 1: Creating job...")
job_id = create_job("Senior Python Backend Developer", job_description)
print(f"Job ID: {job_id}")

print("\nStep 2: Simulating resume processing...")
sample_resume = """
John Doe
john.doe@email.com | +91 9876543210

EXPERIENCE
Software Engineer — TechCorp (2021 - 2024)
- Built REST APIs using Python and FastAPI
- Worked with PostgreSQL and Redis

Junior Developer — StartupXYZ (2019 - 2021)
- Developed frontend features in React

EDUCATION
B.Tech Computer Science — Anna University (2015 - 2019)

SKILLS
Python, FastAPI, React, PostgreSQL, Redis, Docker, Git
"""

parsed = parse_resume_with_ai(sample_resume)
parsed["raw_text"] = sample_resume
score = score_candidate(parsed, job_description)

print("\nParsed candidate:")
print(json.dumps(parsed, indent=2))
print("\nScore result:")
print(json.dumps(score, indent=2))

print("\nStep 3: All candidates in DB:")
candidates = get_all_candidates()
print(f"Total candidates: {len(candidates)}")