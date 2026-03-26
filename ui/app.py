import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.pipeline import (
    create_job, process_resume, get_all_candidates,
    get_all_jobs, override_decision
)
from agent.scorer import draft_interview_email
from db.database import create_db, engine
from db.models import Candidate, JobDescription, Decision
from db.seed import seed_default_jobs
from sqlmodel import Session, select

create_db()
seed_default_jobs()

st.set_page_config(
    page_title="HireIQ — Smart Hiring Pipeline",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #212529; }
    .main { background-color: #F8F9FA; }

    section[data-testid="stSidebar"] {
        background: #E9ECEF;
        border-right: none;
    }
    section[data-testid="stSidebar"] * { color: #212529 !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stSelectbox div(data-testid="baseButton-secondary") {
        color: #212529 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] span { color: #212529 !important; }

    .stTabs [data-baseweb="tab-list"] {
        background: white; border-radius: 12px;
        padding: 4px; gap: 4px; border: 1px solid #DEE2E6;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 20px;
        font-weight: 500; font-size: 14px; color: #495057;
    }
    .stTabs [aria-selected="true"] {
        background: #007BFF !important; color: white !important;
    }
    .stTabs [data-baseweb="tab"] span { color: #495057 !important; }

    .stButton > button {
        background: #007BFF; color: white; border: none;
        border-radius: 8px; padding: 8px 20px;
        font-weight: 500; font-size: 14px; transition: all 0.2s;
    }
    .stButton > button:hover { background: #0056D2; transform: translateY(-1px); }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        border-radius: 8px; border: 1.5px solid #DEE2E6; font-size: 14px; color: #212529;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #495057;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #007BFF;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
    }

    .metric-card {
        background: #FFFFFF; border-radius: 16px;
        padding: 1.25rem; border: 1px solid #DEE2E6; text-align: center;
    }
    .metric-number { font-size: 32px; font-weight: 700; line-height: 1; }
    .metric-label {
        font-size: 12px; color: #495057; font-weight: 600;
        margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .activity-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 0; border-bottom: 1px solid #DEE2E6;
    }
    .activity-row:last-child { border-bottom: none; }
    .activity-dot {
        width: 9px; height: 9px; border-radius: 50%;
        flex-shrink: 0; margin-right: 12px;
    }
    .activity-name { font-size: 14px; font-weight: 600; color: #212529; }
    .activity-sub  { font-size: 12px; color: #495057; margin-top: 2px; font-weight: 500; }

    .badge {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.03em;
    }
    .badge-shortlist { background: #d4edda; color: #28A745; }
    .badge-review    { background: #fff3cd; color: #FFC107; }
    .badge-reject    { background: #f8d7da; color: #DC3545; }
    .badge-pending   { background: #e9ecef; color: #495057; }

    .score-bar-bg {
        background: #DEE2E6; border-radius: 99px;
        height: 6px; margin-top: 4px;
    }
    .score-bar-fill {
        height: 6px; border-radius: 99px;
        background: linear-gradient(90deg, #007BFF, #17A2B8);
    }

    .candidate-card {
        background: #FFFFFF; border-radius: 16px; padding: 1.25rem;
        border: 1px solid #DEE2E6; margin-bottom: 10px; transition: all 0.2s;
    }
    .candidate-card:hover {
        border-color: #007BFF;
        box-shadow: 0 4px 20px rgba(0, 123, 255, 0.15);
    }

    .form-card {
        background: #FFFFFF; border-radius: 16px;
        padding: 1.5rem; border: 1px solid #DEE2E6; margin-bottom: 16px;
    }

    .job-card {
        background: #FFFFFF; border-radius: 12px; padding: 1rem 1.25rem;
        border: 1.5px solid #DEE2E6; margin-bottom: 8px;
    }

    .section-header {
        font-size: 18px; font-weight: 700;
        color: #0F2A4D; margin-bottom: 4px;
    }
    .section-sub {
        font-size: 13px; color: #495057; margin-bottom: 20px; font-weight: 500;
    }

    div[data-testid="stExpander"] {
        background: #FFFFFF; border-radius: 12px;
        border: 1px solid #DEE2E6; margin-bottom: 8px;
    }
    div[data-testid="stExpander"] * { color: #212529 !important; }

    .info-pill {
        background: #F8F9FA; border-radius: 10px; padding: 10px 16px;
        font-size: 13px; color: #495057; margin: 12px 0;
        border: 1px solid #DEE2E6; font-weight: 500;
    }

    .danger-btn > button {
        background: #f8d7da !important; color: #DC3545 !important;
        border: 1px solid #f5c6cb !important;
    }
    .danger-btn > button:hover {
        background: #f5c6cb !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────
def clear_all_candidates():
    with Session(engine) as session:
        for d in session.query(Decision).all():
            session.delete(d)
        for c in session.query(Candidate).all():
            session.delete(c)
        session.commit()

def clear_all_jobs():
    with Session(engine) as session:
        for d in session.query(Decision).all():
            session.delete(d)
        for c in session.query(Candidate).all():
            session.delete(c)
        for j in session.query(JobDescription).all():
            session.delete(j)
        session.commit()

def delete_job(job_id: int):
    with Session(engine) as session:
        job = session.get(JobDescription, job_id)
        if job:
            session.delete(job)
            session.commit()


def delete_candidate(candidate_id: int):
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if candidate:
            decisions = session.exec(
                select(Decision).where(Decision.candidate_id == candidate_id)
            ).all()
            for d in decisions:
                session.delete(d)
            session.delete(candidate)
            session.commit()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='text-align:center; padding:1rem 0 1.5rem;'>
            <div style='font-size:36px; font-weight:700; color:#1f2937;'>HireIQ</div>
            <div style='font-size:22px; font-weight:700; margin-top:8px;'>HireIQ</div>
            <div style='font-size:12px; opacity:0.7; margin-top:4px;'>Smart Hiring Pipeline</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    candidates = get_all_candidates()
    jobs       = get_all_jobs()

    shortlisted = len([c for c in candidates if c["status"] == "SHORTLIST"])
    review      = len([c for c in candidates if c["status"] == "REVIEW"])
    rejected    = len([c for c in candidates if c["status"] == "REJECT"])

    st.markdown(f"""
        <div style='padding:0 0.5rem;'>
            <div style='font-size:11px; opacity:0.7; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:14px;'>Pipeline summary</div>
            <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:13px;'>Shortlisted</span>
                <span style='font-weight:700; color:#86efac;'>{shortlisted}</span>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:13px;'>Under review</span>
                <span style='font-weight:700; color:#fde68a;'>{review}</span>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span style='font-size:13px;'>Rejected</span>
                <span style='font-weight:700; color:#fca5a5;'>{rejected}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
        <div style='padding:0 0.5rem;'>
            <div style='font-size:11px; opacity:0.7; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:12px;'>Active jobs</div>
            {''.join([
                f"<div style='font-size:13px; margin-bottom:6px; opacity:0.9;'>• {j['title']}</div>"
                for j in jobs
            ]) or "<div style='font-size:13px; opacity:0.6;'>No jobs yet</div>"}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("Danger zone"):
        st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
        if st.button("Clear all candidates", use_container_width=True):
            clear_all_candidates()
            st.success("Candidates cleared!")
            st.rerun()
        if st.button("Clear everything", use_container_width=True):
            clear_all_jobs()
            seed_default_jobs()
            st.success("All data cleared and jobs reseeded!")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <div style='padding:0 0.5rem; font-size:11px; opacity:0.5;
                    text-align:center; margin-top:16px;'>
            Powered by Groq + Llama 3.3
        </div>
    """, unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────
st.markdown("""
    <div style='margin-bottom:24px;'>
        <h1 style='font-size:28px; font-weight:700; color:#1f2937; margin:0;'>
            Hiring Pipeline
        </h1>
        <p style='color:#9ca3af; font-size:14px; margin:4px 0 0;'>
            Autonomous resume screening, scoring and scheduling
        </p>
    </div>
""", unsafe_allow_html=True)

# ── Metric row ────────────────────────────────────────────
mc1, mc2, mc3 = st.columns(3)
for col, label, value, color in [
    (mc1, "Shortlisted", shortlisted, "#065f46"),
    (mc2, "Under review", review,      "#92400e"),
    (mc3, "Rejected",     rejected,    "#991b1b"),
]:
    with col:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-number' style='color:{color};'>{value}</div>
                <div class='metric-label'>{label}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Post a Job",
    "Upload Resumes",
    "Candidates"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ══════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Recent activity</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Latest candidates processed by the agent</div>",
        unsafe_allow_html=True
    )

    candidates = get_all_candidates()

    if not candidates:
        st.markdown("""
            <div style='background:white; border-radius:16px; padding:3rem;
                        text-align:center; border:1px solid #ede9fe;'>
                <div style='font-size:48px; color:#4c1d95;'>Processing ready</div>
                <div style='font-size:16px; font-weight:600; color:#1f2937; margin-top:16px;'>
                    Ready to hire smarter
                </div>
                <div style='font-size:13px; color:#9ca3af; margin-top:8px;'>
                    Post a job and upload resumes to get started
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        recent = sorted(candidates, key=lambda x: x["uploaded_at"], reverse=True)[:10]

        rows_html = ""
        for c in recent:
            dot_color = {
                "SHORTLIST": "#10b981",
                "REVIEW":    "#f59e0b",
                "REJECT":    "#ef4444",
                "PENDING":   "#9ca3af"
            }.get(c["status"], "#9ca3af")

            badge_class = {
                "SHORTLIST": "badge-shortlist",
                "REVIEW":    "badge-review",
                "REJECT":    "badge-reject",
                "PENDING":   "badge-pending"
            }.get(c["status"], "badge-pending")

            score_txt = f"{c['score']:.0f}/100" if c["score"] else "Pending"
            role_txt  = c["current_role"] or "Role not specified"

            rows_html += f"""
            <div class="activity-row">
                <div style="display:flex; align-items:center;">
                    <div class="activity-dot" style="background:{dot_color};"></div>
                    <div>
                        <div class="activity-name">{c['name']}</div>
                        <div class="activity-sub">{role_txt} &nbsp;·&nbsp; Score: {score_txt}</div>
                    </div>
                </div>
                <span class="badge {badge_class}">{c['status']}</span>
            </div>
            """

        st.markdown(f"""
            <div style='background:white; border-radius:16px;
                        padding:1.25rem 1.5rem; border:1px solid #ede9fe;'>
                {rows_html}
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Score distribution</div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div class='section-sub'>Overall scores across all candidates</div>",
            unsafe_allow_html=True
        )

        scored = [c for c in candidates if c["score"] is not None]
        if scored:
            df = pd.DataFrame(scored)[["name", "score"]]
            df.columns = ["Candidate", "Score"]
            df = df.sort_values("Score", ascending=False)
            st.bar_chart(df.set_index("Candidate")["Score"])

# ══════════════════════════════════════════════════════════
# TAB 2 — Post a Job
# ══════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Post a new job</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>The agent uses this to score and rank candidates</div>",
        unsafe_allow_html=True
    )

    with st.form("job_form"):
        col1, col2 = st.columns(2)
        with col1:
            job_title       = st.text_input("Job title *", placeholder="e.g. Senior Python Developer")
            department      = st.selectbox("Department", [
                "Engineering", "Product", "Design", "Marketing",
                "Sales", "HR", "Finance", "Operations", "Other"
            ])
            employment_type = st.selectbox("Employment type", [
                "Full-time", "Part-time", "Contract", "Internship", "Freelance"
            ])
        with col2:
            experience_level = st.selectbox("Experience level", [
                "Internship", "Junior (0–2 yrs)", "Mid (2–5 yrs)",
                "Senior (5–8 yrs)", "Lead (8+ yrs)", "Executive"
            ])
            location     = st.selectbox("Location", [
                "Remote", "Onsite", "Hybrid", "Remote-first", "Flexible"
            ])
            salary_range = st.text_input(
                "Salary range (optional)", placeholder="e.g. ₹8–12 LPA"
            )

        job_description = st.text_area(
            "Job description *",
            placeholder="Describe responsibilities, requirements and skills needed...",
            height=220
        )

        submitted = st.form_submit_button("Post job", use_container_width=True)
        if submitted:
            if job_title and job_description:
                full_desc = f"""Job Title: {job_title}
Department: {department}
Experience Level: {experience_level}
Employment Type: {employment_type}
Location: {location}
Salary Range: {salary_range or 'Not specified'}

{job_description}"""
                jid = create_job(job_title, full_desc)
                st.success(f"Job posted successfully! ID: {jid}")
                st.balloons()
            else:
                st.error("Please fill in the job title and description.")

    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>Active job postings</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Manage your current open roles</div>",
        unsafe_allow_html=True
    )

    jobs = get_all_jobs()
    if not jobs:
        st.info("No jobs posted yet.")
    else:
        for j in jobs:
            jc1, jc2 = st.columns([5, 1])
            with jc1:
                st.markdown(f"""
                    <div class='job-card'>
                        <div style='font-size:15px; font-weight:600; color:#1f2937;'>
                            {j['title']}
                        </div>
                        <div style='font-size:12px; color:#9ca3af; margin-top:4px;'>
                            ID: {j['id']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with jc2:
                st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
                if st.button("Delete", key=f"del_{j['id']}"):
                    delete_job(j["id"])
                    st.success(f"Deleted '{j['title']}'")
                    st.rerun()

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        if st.button("Clear all job postings", use_container_width=True):
            with Session(engine) as session:
                for j in session.query(JobDescription).all():
                    session.delete(j)
                session.commit()
            st.success("All job postings cleared!")
            st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 3 — Upload Resumes
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Upload resumes</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>PDF, DOCX, PNG, JPG, JPEG supported · Max 20 MB per file</div>",
        unsafe_allow_html=True
    )

    jobs = get_all_jobs()
    if not jobs:
        st.warning("Post a job first before uploading resumes.")
    else:
        job_titles = [j["title"] for j in jobs]
        job_map    = {j["title"]: j["id"] for j in jobs}

        st.markdown("""
            <div style='font-size:14px; font-weight:500; color:#374151; margin-bottom:6px;'>
                Select job role
            </div>
            <div style='font-size:12px; color:#9ca3af; margin-bottom:14px;'>
                Pick from the list or use the search box below to filter
            </div>
        """, unsafe_allow_html=True)

        selected_title = st.radio(
            "Available roles",
            job_titles,
            label_visibility="collapsed"
        )

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

        search_query = st.text_input(
            "Search matching jobs",
            placeholder="Type to filter — e.g. Python, Designer, Full Stack...",
            key="job_search"
        )

        if search_query:
            matched = [t for t in job_titles if search_query.lower() in t.lower()]
            if matched:
                st.markdown(f"""
                    <div class='info-pill'>
                        {len(matched)} matching role(s) found for
                        <b>"{search_query}"</b>
                    </div>
                """, unsafe_allow_html=True)
                selected_title = st.radio(
                    "Matching roles",
                    matched,
                    label_visibility="collapsed",
                    key="filtered_radio"
                )
            else:
                st.warning(f"No roles found matching '{search_query}'.")
                selected_title = None

        if selected_title:
            active_job_id = job_map[selected_title]
            st.markdown(f"""
                <div class='info-pill'>
                    Resumes will be screened against:
                    <b>{selected_title}</b>
                </div>
            """, unsafe_allow_html=True)
        else:
            active_job_id = None

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Drop resumes here",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Max 20 MB per file · PDF, DOCX, PNG, JPG, JPEG"
        )

        MAX_MB      = 20
        valid_files = []
        if uploaded_files:
            for f in uploaded_files:
                size_mb = len(f.getvalue()) / (1024 * 1024)
                if size_mb > MAX_MB:
                    st.error(
                        f"{f.name} exceeds 20 MB limit "
                        f"({size_mb:.1f} MB) — skipped."
                    )
                else:
                    valid_files.append(f)

        if valid_files:
            st.markdown(f"""
                <div class='info-pill'>
                    {len(valid_files)} valid file(s) ready to screen
                </div>
            """, unsafe_allow_html=True)

            if active_job_id and st.button(
                "Start screening", use_container_width=True
            ):
                progress   = st.progress(0)
                status_box = st.empty()
                results    = []

                for i, file in enumerate(valid_files):
                    status_box.info(f"Processing {file.name}...")

                    save_path = os.path.join("uploads", file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    ext = os.path.splitext(file.name)[1].lower()
                    if ext in [".png", ".jpg", ".jpeg"]:
                        st.info(f"Keeping image format for {file.name} ({ext[1:].upper()}) and processing in source format.")

                    try:
                        result = process_resume(save_path, active_job_id)
                        results.append(result)

                        badge = {
                            "SHORTLIST": "badge-shortlist",
                            "REVIEW":    "badge-review",
                            "REJECT":    "badge-reject"
                        }.get(result["status"], "badge-pending")

                        # Display result with better error handling
                        name_display = result.get('name') or 'Unable to parse'
                        email_display = result.get('email') or 'No email'
                        score_display = result.get('score') or 0
                        
                        # Show warning if there are red flags
                        red_flags_html = ""
                        if result.get('red_flags'):
                            red_flags_html = f"""
                            <div style='background:#fef2f2; border-radius:8px; padding:10px;
                                        font-size:11px; color:#991b1b; margin-top:8px;
                                        border:1px solid #fecaca;'>
                                ⚠️ {result['red_flags']}
                            </div>
                            """

                        st.markdown(f"""
                            <div class='candidate-card'>
                                <div style='display:flex; justify-content:space-between;
                                            align-items:center;'>
                                    <div>
                                        <div style='font-size:15px; font-weight:600;
                                                    color:#1f2937;'>
                                            {name_display}
                                        </div>
                                        <div style='font-size:12px; color:#9ca3af;
                                                    margin-top:2px;'>
                                            {email_display}
                                        </div>
                                    </div>
                                    <div style='text-align:right;'>
                                        <span class='badge {badge}'>
                                            {result['status']}
                                        </span>
                                        <div style='font-size:22px; font-weight:700;
                                                    color:#4c1d95; margin-top:4px;'>
                                            {score_display:.0f}
                                            <span style='font-size:12px;
                                                         color:#9ca3af;'>/100</span>
                                        </div>
                                    </div>
                                </div>
                                <div style='margin-top:12px;'>
                                    <div style='font-size:12px; color:#9ca3af;
                                                margin-bottom:3px;'>
                                        Skills match: {result.get('skills_match', 0):.0f}%
                                    </div>
                                    <div class='score-bar-bg'>
                                        <div class='score-bar-fill'
                                             style='width:{result.get("skills_match", 0)}%;'>
                                        </div>
                                    </div>
                                </div>
                                <div style='margin-top:8px;'>
                                    <div style='font-size:12px; color:#9ca3af;
                                                margin-bottom:3px;'>
                                        Experience fit: {result.get('experience_fit', 0):.0f}%
                                    </div>
                                    <div class='score-bar-bg'>
                                        <div class='score-bar-fill'
                                             style='width:{result.get("experience_fit", 0)}%;'>
                                        </div>
                                    </div>
                                </div>
                                {red_flags_html}
                            </div>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Failed: {file.name} — {str(e)}")

                    progress.progress((i + 1) / len(valid_files))

                status_box.empty()

                st.markdown("""
                    <div style='background:#eef2ff; border-radius:12px; padding:12px;
                                border:1px solid #c7d2fe; margin-top:12px;'>
                        <strong style='color:#1f2937;'>Processing summary</strong><br>
                        <span style='color:#374151;'>Processed files: {processed}</span><br>
                        <span style='color:#374151;'>Accepted candidates: {accepted}</span><br>
                        <span style='color:#374151;'>Under review: {review}</span><br>
                        <span style='color:#374151;'>Rejected: {rejected}</span>
                    </div>
                """.format(
                    processed=len(valid_files),
                    accepted=len([r for r in results if r['status'] == 'SHORTLIST']),
                    review=len([r for r in results if r['status'] == 'REVIEW']),
                    rejected=len([r for r in results if r['status'] == 'REJECT'])
                ), unsafe_allow_html=True)

                st.success(f"Done! {len(results)} resume(s) screened.")
                st.balloons()
                
                import time
                time.sleep(1)
                st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 4 — Candidates
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Candidate pipeline</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Review scores, override decisions and schedule interviews</div>",
        unsafe_allow_html=True
    )

    candidates = get_all_candidates()

    if not candidates:
        st.info("No candidates yet. Upload resumes to get started.")
    else:
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            status_filter = st.multiselect(
                "Filter by status",
                ["SHORTLIST", "REVIEW", "REJECT", "PENDING"],
                default=["SHORTLIST", "REVIEW", "REJECT", "PENDING"]
            )
        with fc2:
            sort_by = st.selectbox(
                "Sort by",
                ["Score (high to low)", "Score (low to high)", "Name"]
            )

        filtered = [c for c in candidates if c["status"] in status_filter]

        if sort_by == "Score (high to low)":
            filtered = sorted(
                filtered, key=lambda x: x["score"] or 0, reverse=True
            )
        elif sort_by == "Score (low to high)":
            filtered = sorted(filtered, key=lambda x: x["score"] or 0)
        else:
            filtered = sorted(filtered, key=lambda x: x["name"])

        for c in filtered:
            badge_class = {
                "SHORTLIST": "badge-shortlist",
                "REVIEW":    "badge-review",
                "REJECT":    "badge-reject",
                "PENDING":   "badge-pending"
            }.get(c["status"], "badge-pending")

            score_val  = c["score"] or 0
            skills_val = c["skills_match"] or 0
            exp_val    = c["experience_fit"] or 0

            with st.expander(
                f"{c['name']}  ·  "
                f"{c['current_role'] or 'N/A'}  ·  "
                f"Score: {score_val:.0f}/100"
            ):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"""
                        <div style='margin-bottom:10px;'>
                            <span class='badge {badge_class}'>{c['status']}</span>
                        </div>
                        <div style='font-size:13px; color:#6b7280; line-height:2;'>
                            <b>Email:</b> {c['email']}<br>
                            <b>Experience:</b> {c['experience_years'] or 'N/A'} years<br>
                            <b>Education:</b> {c.get('education') or 'N/A'}<br>
                            <b>Skills:</b> {c['skills'] or 'N/A'}
                        </div>
                    """, unsafe_allow_html=True)

                    if c.get("red_flags"):
                        st.markdown(f"""
                            <div style='background:#fef2f2; border-radius:8px;
                                        padding:10px 14px; font-size:12px;
                                        color:#991b1b; margin-top:12px;
                                        border:1px solid #fecaca;'>
                                {c['red_flags']}
                            </div>
                        """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div style='font-size:11px; color:#9ca3af; font-weight:500;
                                    text-transform:uppercase; letter-spacing:0.05em;
                                    margin-bottom:10px;'>Scores</div>
                        <div style='font-size:40px; font-weight:700;
                                    color:#4c1d95; line-height:1;'>
                            {score_val:.0f}
                            <span style='font-size:14px; color:#9ca3af;
                                         font-weight:400;'>/100</span>
                        </div>
                        <div style='margin-top:14px;'>
                            <div style='font-size:12px; color:#6b7280; margin-bottom:3px;'>
                                Skills match: {skills_val:.0f}%
                            </div>
                            <div class='score-bar-bg'>
                                <div class='score-bar-fill'
                                     style='width:{skills_val}%;'></div>
                            </div>
                        </div>
                        <div style='margin-top:10px;'>
                            <div style='font-size:12px; color:#6b7280; margin-bottom:3px;'>
                                Experience fit: {exp_val:.0f}%
                            </div>
                            <div class='score-bar-bg'>
                                <div class='score-bar-fill'
                                     style='width:{exp_val}%;'></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                        <div style='font-size:11px; color:#9ca3af; font-weight:500;
                                    text-transform:uppercase; letter-spacing:0.05em;
                                    margin-bottom:10px;'>AI analysis</div>
                        <div style='font-size:12px; color:#6b7280; line-height:1.9;'>
                            <b style='color:#065f46;'>Strengths</b><br>
                            {c['strengths'] or 'N/A'}<br><br>
                            <b style='color:#991b1b;'>Weaknesses</b><br>
                            {c['weaknesses'] or 'N/A'}
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='margin-top:16px;'></div>",
                            unsafe_allow_html=True)

                a1, a2 = st.columns(2)

                with a1:
                    if c["status"] == "SHORTLIST":
                        st.markdown("**Schedule interview**")
                        d    = st.date_input("Date", key=f"d_{c['id']}")
                        t    = st.time_input("Time", key=f"t_{c['id']}")
                        link = st.text_input(
                            "Meet link",
                            value="https://meet.google.com/new",
                            key=f"l_{c['id']}"
                        )
                        if st.button("Generate email", key=f"gen_{c['id']}"):
                            email = draft_interview_email(
                                c["name"], "the position",
                                str(d), str(t), link
                            )
                            st.session_state[f"email_{c['id']}"] = email

                        if f"email_{c['id']}" in st.session_state:
                            st.text_area(
                                "Email draft",
                                st.session_state[f"email_{c['id']}"],
                                height=180,
                                key=f"ea_{c['id']}"
                            )

                with a2:
                    st.markdown("**Override decision**")
                    opts    = ["SHORTLIST", "REVIEW", "REJECT"]
                    cur_idx = opts.index(c["status"]) \
                              if c["status"] in opts else 1
                    new_dec = st.selectbox(
                        "Change to", opts,
                        index=cur_idx,
                        key=f"dec_{c['id']}"
                    )
                    notes = st.text_input(
                        "Reason",
                        placeholder="Optional note",
                        key=f"n_{c['id']}"
                    )
                    if st.button("Apply", key=f"ov_{c['id']}"):
                        override_decision(c["id"], new_dec, notes)
                        st.success("Decision updated!")
                        st.rerun()

                    if st.button("Remove candidate", key=f"rm_{c['id']}"):
                        delete_candidate(c["id"])
                        st.success("Candidate removed from pipeline.")
                        st.rerun()