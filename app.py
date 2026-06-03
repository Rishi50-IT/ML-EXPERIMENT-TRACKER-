"""ML Experiment Tracker — Streamlit entrypoint.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from lib.auth import current_user, logout, require_auth
from lib.db import ensure_indexes, get_db

st.set_page_config(
    page_title="ML Experiment Tracker",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Test DB connectivity early so the user sees a clean error.
try:
    ensure_indexes()
    get_db().command("ping")
except Exception as e:  # noqa: BLE001
    st.error(f"Cannot connect to MongoDB. Check MONGODB_URI in .env\n\n{e}")
    st.stop()

user = require_auth()

with st.sidebar:
    st.markdown(f"### 🔬 ML Tracker")
    st.caption(f"Signed in as **{user}**")
    st.divider()
    st.page_link("app.py", label="🏠 Dashboard")
    st.page_link("pages/1_Projects.py", label="📁 Projects")
    st.page_link("pages/2_New_Run.py", label="➕ New Run")
    st.page_link("pages/3_Compare_Runs.py", label="📊 Compare Runs")
    st.divider()
    if st.button("Sign out", use_container_width=True):
        logout()
        st.rerun()

# ---------------- Dashboard ----------------
st.title("Dashboard")
st.caption("Overview of your machine learning experiments.")

db = get_db()
projects = list(db.projects.find({"owner": user}))
project_ids = [p["_id"] for p in projects]
runs = list(db.runs.find({"project_id": {"$in": project_ids}}).sort("created_at", -1))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Projects", len(projects))
c2.metric("Total runs", len(runs))
c3.metric("Running", sum(1 for r in runs if r["status"] == "running"))
c4.metric("Completed", sum(1 for r in runs if r["status"] == "completed"))

st.divider()

if not projects:
    st.info("You don't have any projects yet. Head to **Projects** to create one.")
else:
    st.subheader("Recent runs")
    if not runs:
        st.caption("No runs yet — log your first from **New Run**.")
    else:
        proj_name = {p["_id"]: p["name"] for p in projects}
        rows = []
        for r in runs[:25]:
            rows.append({
                "Run": r["name"],
                "Project": proj_name.get(r["project_id"], "—"),
                "Status": r["status"],
                "Tags": ", ".join(r.get("tags", [])),
                "Final metrics": ", ".join(
                    f"{k}={v:.4g}" for k, v in (r.get("final_metrics") or {}).items()
                ),
                "Created": r["created_at"].strftime("%Y-%m-%d %H:%M"),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
