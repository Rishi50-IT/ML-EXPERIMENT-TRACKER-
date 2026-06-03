"""New Run page — log a run with params, tags, and optional metric history."""
from __future__ import annotations

import io
import json

import pandas as pd
import streamlit as st

from lib.auth import require_auth
from lib.db import create_run, list_projects, log_metric, update_run

st.set_page_config(page_title="New Run · ML Tracker", page_icon="➕", layout="wide")
user = require_auth()

st.title("➕ Log a new run")

projects = list_projects(user)
if not projects:
    st.warning("Create a project first.")
    st.page_link("pages/1_Projects.py", label="Go to Projects →")
    st.stop()

with st.form("new_run"):
    pid = st.selectbox(
        "Project",
        [str(p["_id"]) for p in projects],
        format_func=lambda k: next(p["name"] for p in projects if str(p["_id"]) == k),
    )
    name = st.text_input("Run name", placeholder="e.g. resnet50-lr1e-3")
    col1, col2 = st.columns(2)
    with col1:
        tags_str = st.text_input("Tags (comma-separated)", placeholder="baseline, resnet")
        status = st.selectbox("Status", ["running", "completed", "failed"], index=1)
    with col2:
        params_json = st.text_area(
            "Hyperparameters (JSON)",
            value='{\n  "lr": 0.001,\n  "batch_size": 32,\n  "epochs": 10\n}',
            height=140,
        )
    notes = st.text_area("Notes", height=80)

    st.markdown("**Optional: metric history CSV**")
    st.caption("Columns: `name,step,value`. Use to log multi-step metrics like loss/accuracy curves.")
    metric_csv = st.file_uploader("Upload metric CSV", type=["csv"])

    st.markdown("**Optional: final metrics (JSON)**")
    final_json = st.text_area(
        "Final metrics",
        value='{\n  "val_accuracy": 0.92,\n  "val_loss": 0.21\n}',
        height=100,
    )

    submitted = st.form_submit_button("Create run", type="primary")

if submitted:
    try:
        params = json.loads(params_json or "{}")
        final_metrics = json.loads(final_json or "{}")
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
        st.stop()
    if not name.strip():
        st.error("Run name is required.")
        st.stop()

    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    run_id = create_run(pid, name.strip(), params, tags, notes.strip(), status)

    if final_metrics:
        update_run(str(run_id), final_metrics={k: float(v) for k, v in final_metrics.items()})

    logged = 0
    if metric_csv is not None:
        try:
            df = pd.read_csv(metric_csv)
            required = {"name", "step", "value"}
            if not required.issubset(df.columns):
                st.error(f"CSV must contain columns: {required}")
            else:
                for _, row in df.iterrows():
                    log_metric(str(run_id), str(row["name"]), int(row["step"]), float(row["value"]))
                    logged += 1
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not parse CSV: {e}")

    st.success(f"Run created. Logged {logged} metric point(s).")
    st.session_state["detail_run_id"] = str(run_id)
    st.page_link("pages/4_Run_Detail.py", label="Open run detail →")

st.divider()
with st.expander("📥 Sample metric CSV"):
    sample = "name,step,value\nloss,0,2.31\nloss,1,1.42\nloss,2,0.88\naccuracy,0,0.10\naccuracy,1,0.55\naccuracy,2,0.78\n"
    st.code(sample, language="csv")
    st.download_button("Download sample.csv", sample, file_name="sample_metrics.csv")
