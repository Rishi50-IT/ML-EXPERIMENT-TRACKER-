"""Seed the database with sample data for the demo user.

Usage:  python seed.py
"""
from __future__ import annotations

import math
import random

from auth import register
from db import create_project, create_run, ensure_indexes, log_metric, update_run

DEMO_USER = "demo"
DEMO_PASS = "demo123"


def main() -> None:
    ensure_indexes()
    ok, msg = register(DEMO_USER, DEMO_PASS)
    print(msg)

    pid = create_project(DEMO_USER, "MNIST Classifier", "Baseline CNN experiments on MNIST.")
    print(f"Project: {pid}")

    configs = [
        {"name": "cnn-lr1e-3", "lr": 1e-3, "batch_size": 32, "epochs": 10, "acc": 0.962},
        {"name": "cnn-lr1e-4", "lr": 1e-4, "batch_size": 32, "epochs": 10, "acc": 0.941},
        {"name": "cnn-lr5e-3", "lr": 5e-3, "batch_size": 64, "epochs": 10, "acc": 0.927},
    ]
    for cfg in configs:
        run_id = create_run(
            str(pid),
            cfg["name"],
            params={"lr": cfg["lr"], "batch_size": cfg["batch_size"], "epochs": cfg["epochs"]},
            tags=["mnist", "cnn"],
            notes="Seeded sample run.",
            status="completed",
        )
        # synthetic curves
        for step in range(cfg["epochs"]):
            loss = 2.3 * math.exp(-0.4 * step) + random.uniform(-0.05, 0.05)
            acc = cfg["acc"] * (1 - math.exp(-0.6 * step)) + random.uniform(-0.02, 0.02)
            log_metric(str(run_id), "loss", step, max(0.01, loss))
            log_metric(str(run_id), "accuracy", step, min(0.999, max(0.0, acc)))
        update_run(
            str(run_id),
            final_metrics={"val_accuracy": cfg["acc"], "val_loss": round(loss, 4)},
        )
        print(f"  Run: {cfg['name']}")

    print("\nDone. Sign in as:")
    print(f"  username: {DEMO_USER}")
    print(f"  password: {DEMO_PASS}")


if __name__ == "__main__":
    main()
