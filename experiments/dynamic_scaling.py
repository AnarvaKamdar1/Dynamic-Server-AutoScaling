"""Example dynamic-workload + dynamic-server-allocation experiment.

Run from the project root:
    python experiments/dynamic_scaling.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import random

from analysis.dynamic import print_dynamic_summary, summarize_dynamic_run
from models.dynamic_mmc import DynamicMMC


# (start_time, end_time, lambda)
WORKLOAD = [
    (0, 50, 2.0),
    (50, 100, 8.0),
    (100, 150, 18.0),
    (150, 200, 5.0),
    (200, 250, 2.0),
]


def run_dynamic_scaling(
    workload=WORKLOAD,
    *,
    service_rate=5.0,
    initial_servers=2,
    horizon=250.0,
    control_interval=10.0,
    low_utilization=0.30,
    high_utilization=0.80,
    queue_high=20.0,
    queue_low=0.0,
    cooldown=20.0,
    min_servers=1,
    max_servers=10,
    seed=42,
):
    """Run a reusable dynamic workload/autoscaling experiment."""
    simulation = DynamicMMC(
        service_rate=service_rate,
        horizon=horizon,
        initial_servers=initial_servers,
        workload=workload,
        control_interval=control_interval,
        low_utilization=low_utilization,
        high_utilization=high_utilization,
        queue_high=queue_high,
        queue_low=queue_low,
        cooldown=cooldown,
        min_servers=min_servers,
        max_servers=max_servers,
        rng=random.Random(seed),
    )
    raw = simulation.run()
    return raw, summarize_dynamic_run(raw)


def main():
    _, summary = run_dynamic_scaling()
    print_dynamic_summary(summary)


if __name__ == "__main__":
    main()
