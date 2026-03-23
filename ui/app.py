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
from db.database import create_db

create_db()

st.set_page_config(
    page_title="Smart Hiring Pipeline",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .status-shortlist { color: #1D9E75; font-weight: 600; }
    .status-review    { color: #BA7517; font-weight: 600; }
    .status-reject    { color: #E24B4A; font-weight: 600; }
    .status-pending   { color: #888780; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("Smart Hiring Pipeline Agent")
st.caption("Autonomous resume screening, scoring and scheduling")

if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None

tab1, tab2, tab3 = st.tabs([
    "Upload Resumes",
    "Candidate Pipeline",
    "Review Queue"
])

with tab1:
    st.subheader("Step 1 — Set up job description")

    jobs = get_all_jobs()
    job_options = {f"{j['id']}: {j['title']}": j["id"] for j in jobs}

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Use existing job**")
        if job_options:
            selected_job_label = st.selectbox(
                "Select a job", list(job_options.keys())
            )
            active_job_id = job_options[selected_job_label]
        else:
            st.info("No jobs yet. Create one on the right.")
            active_job_id = None

    with col2:
        st.markdown("**Create new job**")
        new_job_title = st.text_input("Job title", placeholder="e.g. Senior Python Developer")
        new_job_desc = st.text_area(
            "Job description",
            placeholder="Paste full job description here...",
            height=150
        )
        if st.button("Create Job"):
            if new_job_title and new_job_desc:
                job_id = create_job(new_job_title, new_job_desc)
                st.success(f"Job created! ID: {job_id}")
                st.rerun()
            else:
                st.error("Please fill in both title and description.")

    st.divider()
    st.subheader("Step 2 — Upload resumes")

    if active_job_id:
        uploaded_files = st.file_uploader(
            "Upload PDF or DOCX resumes",
            type=["pdf", "docx"],
            accept_multiple_files=True
        )

        if uploaded_files and st.button("Process Resumes", type="primary"):
            progress = st.progress(0)
            status_box = st.empty()
            results = []

            for i, file in enumerate(uploaded_files):
                status_box.info(f"Processing {file.name}...")

                save_path = os.path.join("uploads", file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())

                try:
                    result = process_resume(save_path, active_job_id)
                    results.append(result)
                    status_box.success(
                        f"{result['name']} — Score: {result['score']} — {result['status']}"
                    )
                except Exception as e:
                    st.error(f"Failed to process {file.name}: {str(e)}")

                progress.progress((i + 1) / len(uploaded_files))

            st.success(f"Done! Processed {len(results)} resumes.")
            st.balloons()
    else:
        st.warning("Create or select a job first.")

with tab2:
    st.subheader("All candidates")

    candidates = get_all_candidates()

    if not candidates:
        st.info("No candidates yet. Upload resumes in the first tab.")
    else:
        total = len(candidates)
        shortlisted = len([c for c in candidates if c["status"] == "SHORTLIST"])
        review = len([c for c in candidates if c["status"] == "REVIEW"])
        rejected = len([c for c in candidates if c["status"] == "REJECT"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("Shortlisted", shortlisted)
        m3.metric("Under review", review)
        m4.metric("Rejected", rejected)

        st.divider()

        status_filter = st.multiselect(
            "Filter by status",
            ["SHORTLIST", "REVIEW", "REJECT", "PENDING"],
            default=["SHORTLIST", "REVIEW", "REJECT", "PENDING"]
        )

        filtered = [c for c in candidates if c["status"] in status_filter]

        for c in filtered:
            status_color = {
                "SHORTLIST": "🟢",
                "REVIEW": "🟡",
                "REJECT": "🔴",
                "PENDING": "⚪"
            }.get(c["status"], "⚪")

            with st.expander(
                f"{status_color} {c['name']} — Score: {c['score'] or 'N/A'} — {c['status']}"
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Profile**")
                    st.write(f"Email: {c['email']}")
                    st.write(f"Role: {c['current_role'] or 'N/A'}")
                    st.write(f"Experience: {c['experience_years'] or 'N/A'} years")
                    st.write(f"Education: {c['education'] or 'N/A'}")

                with col2:
                    st.markdown("**Scores**")
                    if c["score"]:
                        st.metric("Overall", f"{c['score']:.0f}/100")
                        st.metric("Skills match", f"{c['skills_match']:.0f}/100")
                        st.metric("Experience fit", f"{c['experience_fit']:.0f}/100")

                with col3:
                    st.markdown("**AI Analysis**")
                    st.write(f"Strengths: {c['strengths'] or 'N/A'}")
                    st.write(f"Weaknesses: {c['weaknesses'] or 'N/A'}")
                    if c["red_flags"]:
                        st.warning(f"Red flags: {c['red_flags']}")

                if c["status"] == "SHORTLIST":
                    st.divider()
                    st.markdown("**Schedule interview**")
                    icol1, icol2, icol3 = st.columns(3)
                    interview_date = icol1.date_input(
                        "Date", key=f"date_{c['id']}"
                    )
                    interview_time = icol2.time_input(
                        "Time", key=f"time_{c['id']}"
                    )
                    meet_link = icol3.text_input(
                        "Meet link", value="https://meet.google.com/new",
                        key=f"meet_{c['id']}"
                    )

                    if st.button("Generate interview email", key=f"email_{c['id']}"):
                        email = draft_interview_email(
                            c["name"],
                            "the position",
                            str(interview_date),
                            str(interview_time),
                            meet_link
                        )
                        st.text_area("Email draft", email, height=200,
                                     key=f"emaildraft_{c['id']}")

with tab3:
    st.subheader("HR review queue")
    st.caption("Override any AI decision here — corrections are saved for learning")

    candidates = get_all_candidates()
    review_candidates = [c for c in candidates if c["status"] == "REVIEW"]

    if not review_candidates:
        st.success("No candidates pending review!")
    else:
        for c in review_candidates:
            with st.expander(f"⚠️ {c['name']} — Score: {c['score'] or 'N/A'}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"Email: {c['email']}")
                    st.write(f"Role: {c['current_role'] or 'N/A'}")
                    st.write(f"Experience: {c['experience_years'] or 'N/A'} years")
                    st.write(f"Skills: {c['skills'] or 'N/A'}")
                    if c["red_flags"]:
                        st.warning(f"Red flags: {c['red_flags']}")

                with col2:
                    st.markdown("**Override decision**")
                    new_decision = st.selectbox(
                        "New decision",
                        ["SHORTLIST", "REJECT"],
                        key=f"override_{c['id']}"
                    )
                    notes = st.text_input(
                        "Notes", placeholder="Reason for override",
                        key=f"notes_{c['id']}"
                    )
                    if st.button("Apply override", key=f"apply_{c['id']}"):
                        override_decision(c["id"], new_decision, notes)
                        st.success(f"Updated to {new_decision}")
                        st.rerun()