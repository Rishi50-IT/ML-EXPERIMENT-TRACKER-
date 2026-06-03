"""Compare Runs page — side-by-side params & overlaid metric curves."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import require_auth
from components.charts import metric_line_chart
from db import get_metrics, list_projects, list_runs, metric_names

st.set_page_config(page_title="Compare · ML Tracker", page_icon="📊", layout="wide")
user = require_auth()

st.title("📊 Compare runs")

projects = list_projects(user)
if not projects:
    st.info("No projects yet.")
    st.stop()

pid = st.selectbox(
    "Project",
    [str(p["_id"]) for p in projects],
    format_func=lambda k: next(p["name"] for p in projects if str(p["_id"]) == k),
)
runs = list_runs(pid)
if not runs:
    st.info("No runs in this project.")
    st.stop()

picked = st.multiselect(
    "Runs to compare",
    [r["_id"] for r in runs],
    default=[r["_id"] for r in runs[: min(3, len(runs))]],
    format_func=lambda rid: next(r["name"] for r in runs if r["_id"] == rid),
)
if not picked:
    st.stop()

picked_runs = [r for r in runs if r["_id"] in picked]

# Params table
st.subheader("Hyperparameters")
all_keys: set[str] = set()
for r in picked_runs:
    all_keys.update((r.get("params") or {}).keys())
param_rows = []
for r in picked_runs:
    row = {"run": r["name"]}
    for k in sorted(all_keys):
        row[k] = (r.get("params") or {}).get(k, "—")
    param_rows.append(row)
st.dataframe(param_rows, use_container_width=True, hide_index=True)

# Final metrics
st.subheader("Final metrics")
fm_keys: set[str] = set()
for r in picked_runs:
    fm_keys.update((r.get("final_metrics") or {}).keys())
fm_rows = []
for r in picked_runs:
    row = {"run": r["name"]}
    for k in sorted(fm_keys):
        v = (r.get("final_metrics") or {}).get(k)
        row[k] = f"{v:.4g}" if isinstance(v, (int, float)) else "—"
    fm_rows.append(row)
st.dataframe(fm_rows, use_container_width=True, hide_index=True)

# Metric curves
st.subheader("Metric curves")
all_metric_names: set[str] = set()
for r in picked_runs:
    all_metric_names.update(metric_names(str(r["_id"])))
if not all_metric_names:
    st.caption("No step-wise metrics logged for the selected runs.")
    st.stop()

selected_metric = st.selectbox("Metric", sorted(all_metric_names))
frames = []
for r in picked_runs:
    pts = get_metrics(str(r["_id"]), selected_metric)
    if pts:
        frames.append(pd.DataFrame([
            {"step": p["step"], "value": p["value"], "run": r["name"]} for p in pts
        ]))
if frames:
    df = pd.concat(frames, ignore_index=True)
    st.plotly_chart(metric_line_chart(df, title=selected_metric), use_container_width=True)
else:
    st.caption("No data for this metric.")
