# 🔬 ML Experiment Tracker

A lightweight, self-hosted experiment tracker for machine learning runs.
Built with **Streamlit** (UI) and **MongoDB** (storage).

## Features

- Multi-user auth (bcrypt-hashed passwords stored in Mongo)
- **Projects** to group related experiments
- **Runs** with hyperparameters, tags, notes, status, and final metrics
- **Step-wise metric logging** (loss/accuracy curves, etc.)
- **Compare** multiple runs side-by-side (params table + overlaid curves)
- CSV upload to bulk-import metric history
- Dark Plotly charts

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure MongoDB

Copy `.env.example` to `.env` and set your connection string:

```bash
cp .env.example .env
```

```
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net
MONGODB_DB=ml_experiment_tracker
```

For local Mongo: `mongodb://localhost:27017` works out of the box.
For free hosted Mongo: create a cluster at https://www.mongodb.com/atlas.

### 3. (Optional) Seed sample data

```bash
python seed.py
# creates user "demo" / password "demo123" with a sample project
```

### 4. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 and sign in (or create an account).

## Project layout

```
app.py                    # Dashboard + entrypoint
auth.py                   # Login / signup / session
db.py                     # MongoDB data layer
components/charts.py      # Plotly chart helpers
pages/
  1_Projects.py           # Create & browse projects, list runs
  2_New_Run.py            # Log a new run (params, tags, metric CSV)
  3_Compare_Runs.py       # Side-by-side comparison
  4_Run_Detail.py         # Single-run view with curves & notes
seed.py                   # Demo data generator
requirements.txt
.env.example
```

## Logging metrics from your training script

Use `db.py` directly from any Python process that can reach your Mongo URI:

```python
from db import create_run, log_metric, update_run

run_id = create_run(
    project_id="<project_id>",
    name="resnet50-lr1e-3",
    params={"lr": 1e-3, "batch_size": 64},
    tags=["resnet"],
)

for step, (loss, acc) in enumerate(train()):
    log_metric(str(run_id), "loss", step, loss)
    log_metric(str(run_id), "accuracy", step, acc)

update_run(str(run_id), status="completed",
           final_metrics={"val_accuracy": 0.93})
```

## Deploy

- **Streamlit Community Cloud**: push to GitHub, point at `app.py`, add
  `MONGODB_URI` and `MONGODB_DB` as secrets.
- **Docker / any VM**: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`.

## License

MIT
