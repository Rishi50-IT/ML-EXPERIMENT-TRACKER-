"""MongoDB data layer for ML Experiment Tracker."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database

load_dotenv()

_client: Optional[MongoClient] = None


def get_db() -> Database:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client[os.getenv("MONGODB_DB", "ml_experiment_tracker")]


def ensure_indexes() -> None:
    db = get_db()
    db.users.create_index("username", unique=True)
    db.projects.create_index([("owner", ASCENDING), ("name", ASCENDING)], unique=True)
    db.runs.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
    db.metrics.create_index([("run_id", ASCENDING), ("name", ASCENDING), ("step", ASCENDING)])


# ---------- Projects ----------
def list_projects(owner: str) -> list[dict]:
    return list(get_db().projects.find({"owner": owner}).sort("created_at", -1))


def create_project(owner: str, name: str, description: str = "") -> ObjectId:
    res = get_db().projects.insert_one({
        "owner": owner,
        "name": name,
        "description": description,
        "created_at": datetime.utcnow(),
    })
    return res.inserted_id


def get_project(project_id: str) -> Optional[dict]:
    return get_db().projects.find_one({"_id": ObjectId(project_id)})


def delete_project(project_id: str) -> None:
    db = get_db()
    runs = list(db.runs.find({"project_id": ObjectId(project_id)}, {"_id": 1}))
    run_ids = [r["_id"] for r in runs]
    if run_ids:
        db.metrics.delete_many({"run_id": {"$in": run_ids}})
        db.runs.delete_many({"_id": {"$in": run_ids}})
    db.projects.delete_one({"_id": ObjectId(project_id)})


# ---------- Runs ----------
def list_runs(project_id: str) -> list[dict]:
    return list(
        get_db().runs.find({"project_id": ObjectId(project_id)}).sort("created_at", -1)
    )


def create_run(
    project_id: str,
    name: str,
    params: dict[str, Any],
    tags: list[str],
    notes: str = "",
    status: str = "running",
) -> ObjectId:
    res = get_db().runs.insert_one({
        "project_id": ObjectId(project_id),
        "name": name,
        "params": params,
        "tags": tags,
        "notes": notes,
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "final_metrics": {},
    })
    return res.inserted_id


def get_run(run_id: str) -> Optional[dict]:
    return get_db().runs.find_one({"_id": ObjectId(run_id)})


def update_run(run_id: str, **fields) -> None:
    fields["updated_at"] = datetime.utcnow()
    get_db().runs.update_one({"_id": ObjectId(run_id)}, {"$set": fields})


def delete_run(run_id: str) -> None:
    db = get_db()
    db.metrics.delete_many({"run_id": ObjectId(run_id)})
    db.runs.delete_one({"_id": ObjectId(run_id)})


# ---------- Metrics ----------
def log_metric(run_id: str, name: str, step: int, value: float) -> None:
    get_db().metrics.insert_one({
        "run_id": ObjectId(run_id),
        "name": name,
        "step": int(step),
        "value": float(value),
        "ts": datetime.utcnow(),
    })


def get_metrics(run_id: str, name: Optional[str] = None) -> list[dict]:
    q: dict = {"run_id": ObjectId(run_id)}
    if name:
        q["name"] = name
    return list(get_db().metrics.find(q).sort([("name", 1), ("step", 1)]))


def metric_names(run_id: str) -> list[str]:
    return get_db().metrics.distinct("name", {"run_id": ObjectId(run_id)})
