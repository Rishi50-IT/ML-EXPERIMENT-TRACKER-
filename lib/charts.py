"""Reusable Plotly chart helpers."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def metric_line_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """df columns: step, value, run (optional)."""
    color = "run" if "run" in df.columns else None
    fig = px.line(df, x="step", y="value", color=color, markers=True, title=title)
    fig.update_layout(
        template="plotly_dark",
        height=360,
        margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="",
    )
    return fig


def params_table(params: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [{"param": k, "value": str(v)} for k, v in sorted(params.items())]
    )
