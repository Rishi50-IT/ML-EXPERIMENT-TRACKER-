"""Projects page — create / browse / drill into projects."""
from __future__ import annotations

import streamlit as st

from lib.auth import require_auth
from lib.db import create_project, delete_project, list_projects, list_runs

st.set_page_config(page_title="Projects · ML Tracker", page_icon="📁", layout="wide")
user = require_auth()

st.title("📁 Projects")

with st.expander("➕ New project", expanded=False):
    with st.form("new_project"):
        name = st.text_input("Project name")
        desc = st.text_area("Description", height=80)
        if st.form_submit_button("Create", type="primary"):
            if not name.strip():
                st.error("Name is required.")
            else:
                try:
                    create_project(user, name.strip(), desc.strip())
                    st.success("Project created.")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Could not create project: {e}")

projects = list_projects(user)
if not projects:
    st.info("No projects yet.")
    st.stop()

# Project selector — drives the rest of the page.
selected_id = st.session_state.get("selected_project_id")
labels = {str(p["_id"]): p["name"] for p in projects}
default = selected_id if selected_id in labels else str(projects[0]["_id"])
pid = st.selectbox(
    "Project",
    list(labels.keys()),
    index=list(labels.keys()).index(default),
    format_func=lambda k: labels[k],
)
st.session_state["selected_project_id"] = pid
project = next(p for p in projects if str(p["_id"]) == pid)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(project["name"])
    st.caption(project.get("description") or "_No description_")
with col2:
    if st.button("🗑 Delete project", use_container_width=True):
        delete_project(pid)
        st.session_state.pop("selected_project_id", None)
        st.rerun()

st.divider()
st.subheader("Runs")

runs = list_runs(pid)
if not runs:
    st.caption("No runs yet — create one from **New Run**.")
else:
    rows = []
    for r in runs:
        rows.append({
            "id": str(r["_id"]),
            "Name": r["name"],
            "Status": r["status"],
            "Tags": ", ".join(r.get("tags", [])),
            "Params": ", ".join(f"{k}={v}" for k, v in (r.get("params") or {}).items()),
            "Final metrics": ", ".join(
                f"{k}={v:.4g}" for k, v in (r.get("final_metrics") or {}).items()
            ),
            "Created": r["created_at"].strftime("%Y-%m-%d %H:%M"),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True, column_config={"id": None})

    st.markdown("**Open a run**")
    run_pick = st.selectbox(
        "Run",
        [r["_id"] for r in runs],
        format_func=lambda rid: next(r["name"] for r in runs if r["_id"] == rid),
        label_visibility="collapsed",
    )
    if st.button("Open run detail →", type="primary"):
        st.session_state["detail_run_id"] = str(run_pick)
        st.switch_page("pages/4_Run_Detail.py")
