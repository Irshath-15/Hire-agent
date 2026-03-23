import sys
sys.path.append("M:\\Hire-agent")

from agent.parser import parse_resume_with_ai
import json

sample_resume = """
John Doe
john.doe@email.com | +91 9876543210

EXPERIENCE
Software Engineer — TechCorp (2021 - 2024)
- Built REST APIs using Python and FastAPI
- Worked with PostgreSQL and Redis

Junior Developer — StartupXYZ (2019 - 2021)
- Developed frontend features in React
- Wrote unit tests

EDUCATION
B.Tech Computer Science — Anna University (2015 - 2019)

SKILLS
Python, FastAPI, React, PostgreSQL, Redis, Docker, Git
"""

result = parse_resume_with_ai(sample_resume)
print("Parsed result:")
print(json.dumps(result, indent=2))