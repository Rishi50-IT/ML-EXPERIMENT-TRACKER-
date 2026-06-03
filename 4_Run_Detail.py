"""Run Detail page — full view of a single run."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_auth
from components.charts import metric_line_chart, params_table
from db import (
    delete_run,
    get_metrics,
    get_run,
    log_metric,
    metric_names,
    update_run,
)

st.set_page_config(page_title="Run Detail · ML Tracker", page_icon="🔬", layout="wide")
require_auth()

run_id = st.session_state.get("detail_run_id")
if not run_id:
    st.info("Pick a run from **Projects** to view its detail.")
    st.page_link("pages/1_Projects.py", label="← Projects")
    st.stop()

run = get_run(run_id)
if not run:
    st.error("Run not found.")
    st.stop()

c1, c2, c3 = st.columns([4, 2, 1])
with c1:
    st.title(run["name"])
    st.caption(
        f"Status: **{run['status']}** · Created {run['created_at'].strftime('%Y-%m-%d %H:%M')}"
    )
    if run.get("tags"):
        st.write(" ".join(f"`{t}`" for t in run["tags"]))
with c2:
    new_status = st.selectbox(
        "Update status",
        ["running", "completed", "failed"],
        index=["running", "completed", "failed"].index(run["status"]),
    )
    if new_status != run["status"]:
        update_run(run_id, status=new_status)
        st.rerun()
with c3:
    if st.button("🗑 Delete", use_container_width=True):
        delete_run(run_id)
        st.session_state.pop("detail_run_id", None)
        st.switch_page("pages/1_Projects.py")

st.divider()

left, right = st.columns([1, 1])
with left:
    st.subheader("Hyperparameters")
    if run.get("params"):
        st.dataframe(params_table(run["params"]), use_container_width=True, hide_index=True)
    else:
        st.caption("None")
with right:
    st.subheader("Final metrics")
    fm = run.get("final_metrics") or {}
    if fm:
        st.dataframe(
            pd.DataFrame([{"metric": k, "value": v} for k, v in fm.items()]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("None")

st.subheader("Notes")
notes = st.text_area("Notes", value=run.get("notes") or "", label_visibility="collapsed", height=120)
if st.button("Save notes"):
    update_run(run_id, notes=notes)
    st.success("Saved.")

st.divider()
st.subheader("Metric history")
names = metric_names(run_id)
if not names:
    st.caption("No step-wise metrics logged.")
else:
    chosen = st.multiselect("Metrics to plot", names, default=names[: min(2, len(names))])
    for m in chosen:
        pts = get_metrics(run_id, m)
        df = pd.DataFrame([{"step": p["step"], "value": p["value"]} for p in pts])
        st.plotly_chart(metric_line_chart(df, title=m), use_container_width=True)

with st.expander("➕ Log a single metric point"):
    with st.form("log_point"):
        c1, c2, c3 = st.columns(3)
        with c1:
            mname = st.text_input("Name", placeholder="loss")
        with c2:
            mstep = st.number_input("Step", min_value=0, step=1, value=0)
        with c3:
            mval = st.number_input("Value", value=0.0, format="%f")
        if st.form_submit_button("Log point"):
            if mname.strip():
                log_metric(run_id, mname.strip(), int(mstep), float(mval))
                st.rerun()
            else:
                st.error("Name required.")
