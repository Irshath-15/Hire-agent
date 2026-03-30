import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.pipeline import (
    create_job, process_resume, get_all_candidates,
    get_all_jobs, override_decision
)
from agent.scorer import draft_interview_email
from agent.actions import schedule_interview, send_email
from db.database import create_db, engine
from db.models import Candidate, JobDescription, Decision
from sqlmodel import Session
from datetime import datetime
from db.seed import seed_default_jobs
from sqlmodel import Session, select

create_db()
try:
    seed_default_jobs()
except Exception as e:
    print(f"Note: Could not seed jobs (may already exist): {e}")

st.set_page_config(
    page_title="HireIQ — Smart Hiring Pipeline",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E9ECEF;
        background: #0F1419;
    }

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0F1419 0%, #1a1f2e 100%);
    }

    section[data-testid="stSidebar"] {
        background: #1a1f2e;
        border-right: 1px solid #2d3748;
        color: #E9ECEF !important;
    }

    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {
        color: #B0B8C4 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #4F46E5;
        box-shadow: 0 0 12px rgba(79, 70, 229, 0.1);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 14px;
        color: #B0B8C4;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
        color: white !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%);
        transform: translateY(-1px);
        box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3);
    }

    .stButton > button.primary {
        background: #4F46E5;
    }

    .stAlert, .stNotification, .info-pill {
        border-color: #2d3748;
        background-color: #1a1f2e;
        color: #E9ECEF;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 8px;
        border: 1.5px solid #2d3748;
        font-size: 14px;
        color: #E9ECEF;
        background-color: #0F1419;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #718096;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
    }

    .metric-card,
    .candidate-card,
    .form-card,
    .job-card,
    div[data-testid="stExpander"],
    .info-pill {
        background: #1a1f2e;
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid #4F46E5;
        box-shadow: 0 8px 16px rgba(79, 70, 229, 0.1), 0 0 20px rgba(79, 70, 229, 0.05);
    }

    .metric-number { font-size: 48px; font-weight: 700; line-height: 1; color: #FFFFFF; }
    .metric-label { font-size: 12px; color: #B0B8C4; font-weight: 600; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
    .section-header { font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px; }
    .section-sub { font-size: 13px; color: #B0B8C4; margin-bottom: 20px; font-weight: 500; }

    .activity-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #2d3748; }
    .activity-row:last-child { border-bottom: none; }
    .activity-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; margin-right: 12px; }
    .activity-name { font-size: 14px; font-weight: 600; color: #FFFFFF; }
    .activity-sub { font-size: 12px; color: #B0B8C4; margin-top: 2px; font-weight: 500; }

    .badge-shortlist { background: #065f46; color: #10b981; }
    .badge-review { background: #78350f; color: #f59e0b; }
    .badge-reject { background: #7f1d1d; color: #ef4444; }
    .badge-pending { background: #0c4a6e; color: #22d3ee; }

    .danger-btn > button { background: #DC2626 !important; color: #FFFFFF !important; border: 1px solid #991b1b !important; font-weight: 600; }
    .danger-btn > button:hover { background: #991b1b !important; box-shadow: 0 8px 16px rgba(220, 38, 38, 0.3); }
    
    .danger-expander {
        border: 1.5px solid #DC2626 !important;
        border-radius: 12px !important;
        box-shadow: 0 0 16px rgba(220, 38, 38, 0.2) !important;
    }
    
    .danger-expander-header {
        color: #ef4444 !important;
        font-weight: 600 !important;
    }
    
    .stMultiSelect > div > div {
        border-radius: 8px;
        border: 1.5px solid #2d3748;
        background-color: #0F1419;
    }

    .stMultiSelect label {
        color: #E9ECEF !important;
    }

    .score-bar-bg { background: #2d3748; border-radius: 8px; height: 8px; overflow: hidden; }
    .score-bar-fill { background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%); height: 100%; transition: width 0.3s ease; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────
def clear_all_candidates():
    try:
        with Session(engine) as session:
            for d in session.query(Decision).all():
                session.delete(d)
            for c in session.query(Candidate).all():
                session.delete(c)
            session.commit()
    except Exception as e:
        st.error(f"Error clearing candidates: {str(e)}")

def clear_all_jobs():
    try:
        with Session(engine) as session:
            for d in session.query(Decision).all():
                session.delete(d)
            for c in session.query(Candidate).all():
                session.delete(c)
            for j in session.query(JobDescription).all():
                session.delete(j)
            session.commit()
    except Exception as e:
        st.error(f"Error clearing data: {str(e)}")

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
            <div style='font-size:36px; font-weight:700; color:#FFFFFF;'>HireIQ</div>
            <div style='font-size:12px; opacity:0.8; margin-top:8px; color:#B0B8C4;'>Smart Hiring Pipeline</div>
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
                        letter-spacing:0.08em; margin-bottom:14px; color:#B0B8C4;'>Pipeline summary</div>
            <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:13px; color:#FFFFFF;'>Shortlisted</span>
                <span style='font-weight:700; color:#10b981;'>{shortlisted}</span>
            </div>
            <div style='display:flex; justify-content:space-between; margin-bottom:10px;'>
                <span style='font-size:13px; color:#FFFFFF;'>Under review</span>
                <span style='font-weight:700; color:#f59e0b;'>{review}</span>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span style='font-size:13px; color:#FFFFFF;'>Rejected</span>
                <span style='font-weight:700; color:#ef4444;'>{rejected}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
        <div style='padding:0 0.5rem;'>
            <div style='font-size:11px; opacity:0.7; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:12px; color:#B0B8C4;'>Active jobs</div>
            {''.join([
                f"<div style='font-size:13px; margin-bottom:6px; opacity:0.9; color:#FFFFFF;'>• {j['title']}</div>"
                for j in jobs
            ]) or "<div style='font-size:13px; opacity:0.6; color:#718096;'>No jobs yet</div>"}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
        <div style='border: 1.5px solid #DC2626; border-radius: 12px; padding: 0.75rem; 
                    background: rgba(220, 38, 38, 0.05); box-shadow: 0 0 16px rgba(220, 38, 38, 0.15);'>
    """, unsafe_allow_html=True)
    
    with st.expander(" Danger zone", expanded=False):
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
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='padding:0 0.5rem; font-size:11px; opacity:0.5;
                    text-align:center; margin-top:16px; color:#B0B8C4;'>
            Powered by Groq + Llama 3.3
        </div>
    """, unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────
st.markdown("""
    <div style='margin-bottom:24px;'>
        <h1 style='font-size:28px; font-weight:700; color:#FFFFFF; margin:0;'>
            Hiring Pipeline
        </h1>
        <p style='color:#B0B8C4; font-size:14px; margin:4px 0 0;'>
            Autonomous resume screening, scoring and scheduling
        </p>
    </div>
""", unsafe_allow_html=True)

# ── Metric row ────────────────────────────────────────────
mc1, mc2, mc3 = st.columns(3)
for col, label, value, color in [
    (mc1, "Shortlisted", shortlisted, "#10b981"),
    (mc2, "Under review", review,      "#f59e0b"),
    (mc3, "Rejected",     rejected,    "#ef4444"),
]:
    with col:
        st.markdown(f"""
            <div class='metric-card' style='border-left: 4px solid {color};'>
                <div class='metric-number'>{value}</div>
                <div class='metric-label'>{label}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Dashboard",
    "Post a Job",
    "Upload Resumes",
    "Candidates",
    "Database"
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
            <div style='background:#1a1f2e; border-radius:16px; padding:3rem;
                        text-align:center; border:1px solid #2d3748;'>
                <div style='font-size:48px;'>🚀</div>
                <div style='font-size:16px; font-weight:600; color:#E9ECEF; margin-top:16px;'>
                    Ready to hire smarter
                </div>
                <div style='font-size:13px; color:#B0B8C4; margin-top:8px;'>
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
                "PENDING":   "#22d3ee"
            }.get(c["status"], "#22d3ee")

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
            <div style='background:#1a1f2e; border-radius:12px;
                        padding:1.25rem 1.5rem; border:1px solid #2d3748;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.2);'>
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
            
            fig = px.bar(
                df,
                x="Candidate",
                y="Score",
                title="Candidate Scores Overview",
                labels={"Score": "Score (0-100)", "Candidate": "Candidate Name"},
                color="Score",
                color_continuous_scale=["#DC3545", "#FFC107", "#28A745"],
                range_color=[0, 100]
            )
            
            fig.update_layout(
                plot_bgcolor="#1a1f2e",
                paper_bgcolor="#0F1419",
                font=dict(family="Inter, sans-serif", size=12, color="#E9ECEF"),
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="#2d3748",
                    title_font=dict(size=14, color="#E9ECEF"),
                    tickfont=dict(size=11, color="#B0B8C4")
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="#2d3748",
                    range=[0, 100],
                    title_font=dict(size=14, color="#E9ECEF"),
                    tickfont=dict(size=11, color="#B0B8C4")
                ),
                hovermode="x unified",
                height=400,
                margin=dict(l=60, r=20, t=60, b=80)
            )
            
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>Score: %{y}/100<extra></extra>",
                marker=dict(line=dict(color="#4F46E5", width=0.5))
            )
            
            st.plotly_chart(fig, use_container_width=True)

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
                        <div style='font-size:15px; font-weight:600; color:#FFFFFF;'>
                            {j['title']}
                        </div>
                        <div style='font-size:12px; color:#B0B8C4; margin-top:4px;'>
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
            <div style='font-size:14px; font-weight:500; color:#E9ECEF; margin-bottom:6px;'>
                Select job role
            </div>
            <div style='font-size:12px; color:#B0B8C4; margin-bottom:14px;'>
                Pick from the list or use the search box below to filter
            </div>
        """, unsafe_allow_html=True)

        selected_titles = st.multiselect(
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

        resume_search_keyword = st.text_input(
            "Resume keyword or phrase",
            placeholder="Type text to check inside uploaded resumes (e.g., SQL, React, AWS)",
            key="resume_search_keyword"
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
                selected_titles = st.multiselect(
                    "Matching roles",
                    matched,
                    label_visibility="collapsed",
                    key="filtered_multiselect"
                )
            else:
                st.warning(f"No roles found matching '{search_query}'.")
                selected_titles = []

        if selected_titles:
            active_job_ids = [job_map[title] for title in selected_titles]
            jobs_list = ", ".join(selected_titles)
            st.markdown(f"""
                <div class='info-pill'>
                    Resumes will be screened against:
                    <b>{jobs_list}</b>
                </div>
            """, unsafe_allow_html=True)
        else:
            active_job_ids = []

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

            if active_job_ids and st.button(
                "Start screening", use_container_width=True
            ):
                # Custom animated spinner and message
                spinner_html = """
                <div style='display:flex; flex-direction:column; align-items:center; margin-top:32px; margin-bottom:24px;'>
                  <div class='custom-spinner' style='margin-bottom:18px;'>
                    <div style='width:60px; height:60px; border:6px solid #6366f1; border-top:6px solid #fbbf24; border-radius:50%; animation: spin 1s linear infinite;'></div>
                  </div>
                  <div style='font-size:17px; color:#6366f1; font-weight:600;'>Initializing AI screening...</div>
                  <div style='font-size:13px; color:#9ca3af; margin-top:6px;'>Preparing to analyze resumes with advanced AI</div>
                </div>
                """
                spinner_box = st.empty()
                spinner_box.markdown(spinner_html, unsafe_allow_html=True)

                results = []
                for i, file in enumerate(valid_files):
                    # Update spinner with file name and process details
                    spinner_box.markdown(f"""
                        <div style='display:flex; flex-direction:column; align-items:center; margin-top:32px; margin-bottom:24px;'>
                          <div class='custom-spinner' style='margin-bottom:18px;'>
                            <div style='width:60px; height:60px; border:6px solid #6366f1; border-top:6px solid #fbbf24; border-radius:50%; animation: spin 1s linear infinite;'></div>
                          </div>
                          <div style='font-size:17px; color:#6366f1; font-weight:600;'>Processing <span style="color:#fbbf24">{file.name}</span></div>
                          <div style='font-size:13px; color:#9ca3af; margin-top:6px; text-align:center;'>
                            AI is working in the background:<br>
                            • Parsing resume text and extracting content<br>
                            • Analyzing skills, experience, and qualifications<br>
                            • Scoring candidate fit against job requirements<br>
                            • Generating detailed feedback and recommendations
                          </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Create uploads directory if it doesn't exist
                    upload_dir = "uploads"
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir, exist_ok=True)

                    save_path = os.path.join("uploads", file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    ext = os.path.splitext(file.name)[1].lower()
                    if ext in [".png", ".jpg", ".jpeg"]:
                        st.info(f"Keeping image format for {file.name} ({ext[1:].upper()}) and processing in source format.")

                    try:
                        # Process resume against all selected jobs and use the first one's result
                        result = process_resume(save_path, active_job_ids[0])
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
                        status = result.get('status', 'ERROR')
                        
                        # Show error details if parsing failed
                        if status == 'ERROR':
                            error_msg = result.get('error') or result.get('message') or 'Unknown error'
                            st.warning(f"⚠️ **Processing Error for {file.name}**\n\n{error_msg}")
                            continue
                        
                        # Check if it's an image-based PDF that couldn't be processed
                        resume_text = (result.get('raw_text') or '').lower()
                        if "[image-based pdf]" in resume_text or "[ocr-failed]" in resume_text or "[error]" in resume_text:
                            st.warning(f"""
                            ⚠️ **Could Not Extract Text from PDF**
                            
                            **File:** {file.name}
                            
                            The system tried to extract text but was unsuccessful. This could be due to:
                            - Scanned/image-based PDF without OCR conversion
                            - Encrypted or protected PDF
                            - PDF with complex formatting
                            
                            **Solutions:**
                            1. Convert scanned PDF to searchable format: [iLovePDF OCR](https://www.ilovepdf.com/ocr)
                            2. Export original document as "Save as PDF"
                            3. Use PDF with copy-paste enabled
                            """)
                            continue
                        
                        # Search keyword in resume text
                        keyword_result_html = ""
                        keyword = resume_search_keyword.strip().lower() if resume_search_keyword else ''
                        if keyword:
                            if keyword in resume_text:
                                keyword_result_html = f"<div style='background:#e6ffed; border-radius:8px; padding:10px; color:#065f46; border:1px solid #a7f3d0; margin-top:8px;'>Keyword '{resume_search_keyword}' was found in resume.</div>"
                            else:
                                keyword_result_html = f"<div style='background:#fff4e5; border-radius:8px; padding:10px; color:#92400e; border:1px solid #fde68a; margin-top:8px;'>Keyword '{resume_search_keyword}' not found in resume.</div>"

                        # Show warning if there are red flags
                        red_flags_html = ""
                        if result.get('red_flags'):
                            red_flags_html = f"""
                            <div style='background:#7f1d1d; border-radius:8px; padding:10px;
                                        font-size:11px; color:#fca5a5; margin-top:8px;
                                        border:1px solid #991b1b;'>
                                ⚠️ {result['red_flags']}
                            </div>
                            """

                        st.markdown(f"""
                            <div class='candidate-card'>
                                <div style='display:flex; justify-content:space-between;
                                            align-items:center;'>
                                    <div>
                                        <div style='font-size:15px; font-weight:600;
                                                    color:#FFFFFF;'>
                                            {name_display}
                                        </div>
                                        <div style='font-size:12px; color:#B0B8C4;
                                                    margin-top:2px;'>
                                            {email_display}
                                        </div>
                                    </div>
                                    <div style='text-align:right;'>
                                        <span class='badge {badge}'>
                                            {result['status']}
                                        </span>
                                        <div style='font-size:22px; font-weight:700;
                                                    color:#FFFFFF; margin-top:4px;'>
                                            {score_display:.0f}
                                            <span style='font-size:12px;
                                                         color:#B0B8C4;'>/100</span>
                                        </div>
                                    </div>
                                </div>
                                <div style='margin-top:12px;'>
                                    <div style='font-size:12px; color:#B0B8C4;
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
                                    <div style='font-size:12px; color:#B0B8C4;
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
                                {keyword_result_html}
                            </div>
                        """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"Failed: {file.name} — {str(e)}")

                spinner_box.empty()

                st.markdown("""
                    <div style='background:#1a1f2e; border-radius:12px; padding:12px;
                                border:1px solid #2d3748; margin-top:12px;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.2);'>
                        <strong style='color:#E9ECEF;'>Processing summary</strong><br>
                        <span style='color:#B0B8C4;'>Processed files: {processed}</span><br>
                        <span style='color:#B0B8C4;'>Accepted candidates: {accepted}</span><br>
                        <span style='color:#B0B8C4;'>Under review: {review}</span><br>
                        <span style='color:#B0B8C4;'>Rejected: {rejected}</span>
                    </div>
                """.format(
                    processed=len(valid_files),
                    accepted=len([r for r in results if r['status'] == 'SHORTLIST']),
                    review=len([r for r in results if r['status'] == 'REVIEW']),
                    rejected=len([r for r in results if r['status'] == 'REJECT'])
                ), unsafe_allow_html=True)

                st.success(f"Done! {len(results)} resume(s) screened.")
                
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
                        <div style='font-size:13px; color:#E9ECEF; line-height:2;'>
                            <b style='color:#FFFFFF;'>Email:</b> {c['email']}<br>
                            <b style='color:#FFFFFF;'>Experience:</b> {c['experience_years'] or 'N/A'} years<br>
                            <b style='color:#FFFFFF;'>Education:</b> {c.get('education') or 'N/A'}<br>
                            <b style='color:#FFFFFF;'>Skills:</b> {c['skills'] or 'N/A'}<br>
                            <b style='color:#FFFFFF;'>Scheduled:</b> {c.get('scheduled_at') or 'Not scheduled'}<br>
                            <b style='color:#FFFFFF;'>Calendar:</b> {f"<a href=\"{c.get('calendar_link')}\" style=\"color:#4F46E5;\" target=\"_blank\">Link</a>" if c.get('calendar_link') else 'N/A'}<br>
                            <b style='color:#FFFFFF;'>Email:</b> <span style='color:{'#10b981' if c.get('email_status')=='sent' else '#f59e0b' if c.get('email_status')=='skipped' else '#ef4444'};'>{c.get('email_status') or 'Not sent'}</span>
                            {f"<span style='color:#ef4444;'> ({c.get('email_error')})</span>" if c.get('email_error') else ''}
                        </div>
                    """, unsafe_allow_html=True)

                    if c.get("red_flags"):
                        st.markdown(f"""
                            <div style='background:#7f1d1d; border-radius:8px;
                                        padding:10px 14px; font-size:12px;
                                        color:#fca5a5; margin-top:12px;
                                        border:1px solid #991b1b;'>
                                {c['red_flags']}
                            </div>
                        """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div style='font-size:11px; color:#B0B8C4; font-weight:500;
                                    text-transform:uppercase; letter-spacing:0.05em;
                                    margin-bottom:10px;'>Scores</div>
                        <div style='font-size:40px; font-weight:700;
                                    color:#FFFFFF; line-height:1;'>
                            {score_val:.0f}
                            <span style='font-size:14px; color:#B0B8C4;
                                         font-weight:400;'>/100</span>
                        </div>
                        <div style='margin-top:14px;'>
                            <div style='font-size:12px; color:#B0B8C4; margin-bottom:3px;'>
                                Skills match: {skills_val:.0f}%
                            </div>
                            <div class='score-bar-bg'>
                                <div class='score-bar-fill'
                                     style='width:{skills_val}%;'></div>
                            </div>
                        </div>
                        <div style='margin-top:10px;'>
                            <div style='font-size:12px; color:#B0B8C4; margin-bottom:3px;'>
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
                        <div style='font-size:11px; color:#B0B8C4; font-weight:500;
                                    text-transform:uppercase; letter-spacing:0.05em;
                                    margin-bottom:10px;'>AI analysis</div>
                        <div style='font-size:12px; color:#E9ECEF; line-height:1.9;'>
                            <b style='color:#10b981;'>Strengths</b><br>
                            {c['strengths'] or 'N/A'}<br><br>
                            <b style='color:#ef4444;'>Weaknesses</b><br>
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
                                c["name"], c.get("current_role", "the position"),
                                d.strftime('%Y-%m-%d'), t.strftime('%I:%M %p'), link
                            )
                            st.session_state[f"email_{c['id']}"] = email

                        if st.button("Schedule & Send", key=f"send_{c['id']}"):
                            schedule_result = schedule_interview(
                                c["name"], c["email"], c.get("current_role", "Interview"),
                                d.strftime('%Y-%m-%d'), t.strftime('%I:%M %p')
                            )

                            email_body = draft_interview_email(
                                c["name"], c.get("current_role", "the position"),
                                schedule_result.get("interview_date", d.strftime('%Y-%m-%d')),
                                schedule_result.get("interview_time", t.strftime('%I:%M %p')),
                                schedule_result.get("calendar_link", link)
                            )

                            email_result = send_email(
                                c["email"],
                                f"Interview Invitation: {c.get('current_role', 'Interview')}",
                                email_body
                            )

                            # Update candidate record in database
                            with Session(engine) as session:
                                candidate = session.get(Candidate, c["id"])
                                if candidate:
                                    candidate.scheduled_at = datetime.utcnow()
                                    candidate.calendar_link = schedule_result.get("calendar_link")
                                    candidate.email_status = email_result.get("status")
                                    candidate.email_error = email_result.get("error") or email_result.get("message")
                                    session.add(candidate)
                                    session.commit()

                            st.success("Scheduled and sent candidate invitation")
                            st.markdown(
                                f"- Calendar link: {schedule_result.get('calendar_link')}<br>"
                                f"- Email status: {email_result.get('status')}<br>"
                                f"- Error: {email_result.get('error', '')}",
                                unsafe_allow_html=True
                            )
                            st.rerun()

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

# ══════════════════════════════════════════════════════════
# TAB 5 — Database Viewer
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Database Viewer</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>View and manage all records in the hiring system</div>",
        unsafe_allow_html=True
    )

    db_tab1, db_tab2, db_tab3 = st.tabs(["Candidates", "Jobs", "Decisions"])

    # ── Database Tab 1: Candidates ────────────────────
    with db_tab1:
        st.markdown("### All Candidates")
        candidates_data = get_all_candidates()
        
        if candidates_data:
            df_candidates = pd.DataFrame(candidates_data)
            
            # Display stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Candidates", len(df_candidates))
            with col2:
                st.metric("Shortlisted", len([c for c in df_candidates["status"] if c == "SHORTLIST"]))
            with col3:
                st.metric("Under Review", len([c for c in df_candidates["status"] if c == "REVIEW"]))
            with col4:
                st.metric("Rejected", len([c for c in df_candidates["status"] if c == "REJECT"]))
            
            # Display table
            st.markdown("---")
            st.dataframe(
                df_candidates[["id", "name", "email", "current_role", "score", "status", "uploaded_at"]].sort_values("id", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            # Download CSV
            csv = df_candidates.to_csv(index=False)
            st.download_button(
                label="📥 Download Candidates CSV",
                data=csv,
                file_name="candidates.csv",
                mime="text/csv"
            )
        else:
            st.info("No candidates in database yet.")

    # ── Database Tab 2: Jobs ───────────────────────────
    with db_tab2:
        st.markdown("### All Job Postings")
        jobs_data = get_all_jobs()
        
        if jobs_data:
            df_jobs = pd.DataFrame(jobs_data)
            
            st.metric("Total Jobs", len(df_jobs))
            st.markdown("---")
            
            st.dataframe(
                df_jobs[["id", "title", "description"]].sort_values("id", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            csv = df_jobs.to_csv(index=False)
            st.download_button(
                label="📥 Download Jobs CSV",
                data=csv,
                file_name="jobs.csv",
                mime="text/csv"
            )
        else:
            st.info("No jobs posted yet.")

    # ── Database Tab 3: Decisions ──────────────────────
    with db_tab3:
        st.markdown("### All Decisions")
        create_db()
        
        with Session(engine) as session:
            decisions = session.exec(select(Decision)).all()
            
        if decisions:
            decisions_list = [
                {
                    "id": d.id,
                    "candidate_id": d.candidate_id,
                    "original_decision": d.original_decision,
                    "notes": d.notes,
                    "created_at": str(d.created_at) if hasattr(d, 'created_at') else "N/A"
                }
                for d in decisions
            ]
            df_decisions = pd.DataFrame(decisions_list)
            
            st.metric("Total Decisions", len(df_decisions))
            st.markdown("---")
            
            st.dataframe(
                df_decisions.sort_values("id", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            csv = df_decisions.to_csv(index=False)
            st.download_button(
                label="📥 Download Decisions CSV",
                data=csv,
                file_name="decisions.csv",
                mime="text/csv"
            )
        else:
            st.info("No decisions recorded yet.")
