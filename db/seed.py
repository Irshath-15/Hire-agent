from sqlmodel import Session, select
from db.database import engine, create_db
from db.models import JobDescription

DEFAULT_JOBS = [
    {
        "title": "Senior Python Backend Developer",
        "description": """Job Title: Senior Python Backend Developer
Department: Engineering
Experience Level: Senior (5–8 yrs)
Employment Type: Full-time
Location: Remote
Salary Range: ₹12–20 LPA

We are looking for a Senior Python Backend Developer to build and scale our backend systems.

Responsibilities:
- Design and build scalable REST APIs using FastAPI or Django
- Work with PostgreSQL, Redis and cloud infrastructure
- Mentor junior developers and conduct code reviews
- Collaborate with frontend and DevOps teams

Requirements:
- 5+ years of Python experience
- Strong knowledge of FastAPI or Django
- Experience with PostgreSQL and Redis
- Familiarity with Docker, AWS or GCP
- Strong problem-solving and communication skills"""
    },
    {
        "title": "Web Designer",
        "description": """Job Title: Web Designer
Department: Design
Experience Level: Mid (2–5 yrs)
Employment Type: Full-time
Location: Hybrid
Salary Range: ₹6–10 LPA

We are looking for a creative Web Designer to craft beautiful and functional web experiences.

Responsibilities:
- Design responsive web pages and landing pages
- Create wireframes, mockups and prototypes
- Collaborate with developers to implement designs
- Maintain brand consistency across all digital assets

Requirements:
- 2+ years of web design experience
- Proficiency in Figma, Adobe XD or Sketch
- Strong knowledge of HTML and CSS
- Eye for typography, color and layout
- Portfolio of previous web design work"""
    },
    {
        "title": "Graphic Designer",
        "description": """Job Title: Graphic Designer
Department: Design
Experience Level: Mid (2–5 yrs)
Employment Type: Full-time
Location: Onsite
Salary Range: ₹5–9 LPA

We need a talented Graphic Designer to create compelling visual content for our brand.

Responsibilities:
- Design social media graphics, banners and marketing materials
- Create brand identity assets including logos and style guides
- Work with the marketing team on campaigns
- Produce print and digital design assets

Requirements:
- 2+ years of graphic design experience
- Proficiency in Adobe Photoshop, Illustrator and InDesign
- Strong understanding of visual hierarchy and branding
- Ability to manage multiple projects simultaneously
- Strong portfolio demonstrating creative range"""
    },
    {
        "title": "Full Stack Developer",
        "description": """Job Title: Full Stack Developer
Department: Engineering
Experience Level: Mid (2–5 yrs)
Employment Type: Full-time
Location: Remote
Salary Range: ₹10–16 LPA

We are looking for a Full Stack Developer comfortable working across the entire web stack.

Responsibilities:
- Build and maintain frontend interfaces using React or Vue
- Develop backend APIs using Node.js or Python
- Work with SQL and NoSQL databases
- Deploy and monitor applications on cloud platforms

Requirements:
- 3+ years of full stack development experience
- Strong knowledge of React or Vue on the frontend
- Backend experience with Node.js, Python or similar
- Familiarity with PostgreSQL or MongoDB
- Experience with Git, Docker and CI/CD pipelines"""
    }
]

def seed_default_jobs():
    create_db()
    with Session(engine) as session:
        for job_data in DEFAULT_JOBS:
            existing = session.exec(
                select(JobDescription).where(
                    JobDescription.title == job_data["title"]
                )
            ).first()
            if not existing:
                job = JobDescription(
                    title=job_data["title"],
                    description=job_data["description"]
                )
                session.add(job)
        session.commit()
        print("Default jobs seeded!")

if __name__ == "__main__":
    seed_default_jobs()