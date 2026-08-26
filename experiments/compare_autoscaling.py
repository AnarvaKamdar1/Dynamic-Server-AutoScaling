"""Monte Carlo comparison of static and dynamic server allocation.

Run from the project root:
    python experiments/compare_autoscaling.py

The experiment compares:
    A. Static c=2 (under-provisioned baseline)
    B. Static c=6 (over-provisioned baseline)
    C. Dynamic autoscaling (current controller)

The same workload and matched random seeds are used across all three systems
for every replication. Results are written to experiments/results/.
"""

import csv
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.dynamic import summarize_dynamic_run
from analysis.experiment_metrics import summarize_run, interval_waiting_times
from models.dynamic_mmc import DynamicMMC
from models.workload_mmc import WorkloadMMC

WORKLOAD = [
    (0, 50, 2.0),
    (50, 100, 8.0),
    (100, 150, 18.0),
    (150, 200, 5.0),
    (200, 250, 2.0),
]

CONFIG = {
    "static_c2": {"label": "Static c=2", "type": "static", "servers": 2},
    "static_c6": {"label": "Static c=6", "type": "static", "servers": 6},
    "dynamic": {"label": "Dynamic autoscaling", "type": "dynamic"},
}


def run_experiments(
    *,
    workload=WORKLOAD,
    service_rate=5.0,
    horizon=250.0,
    control_interval=10.0,
    repetitions=100,
    seed=42,
    sla_wait_threshold=1.0,
    dynamic_initial_servers=2,
    dynamic_min_servers=1,
    dynamic_max_servers=10,
    low_utilization=0.30,
    high_utilization=0.80,
    queue_high=20.0,
    queue_low=0.0,
    cooldown=20.0,
):
    master_rng = random.Random(seed)
    replication_seeds = [master_rng.randrange(2**63) for _ in range(repetitions)]
    all_results = {}

    for key, config in CONFIG.items():
        summaries = []
        interval_accumulator = []
        event_counts = []

        for run_seed in replication_seeds:
            rng = random.Random(run_seed)
            if config["type"] == "static":
                model = WorkloadMMC(
                    service_rate=service_rate,
                    horizon=horizon,
                    num_servers=config["servers"],
                    workload=workload,
                    control_interval=control_interval,
                    rng=rng,
                )
            else:
                model = DynamicMMC(
                    service_rate=service_rate,
                    horizon=horizon,
                    initial_servers=dynamic_initial_servers,
                    workload=workload,
                    control_interval=control_interval,
                    low_utilization=low_utilization,
                    high_utilization=high_utilization,
                    queue_high=queue_high,
                    queue_low=queue_low,
                    cooldown=cooldown,
                    min_servers=dynamic_min_servers,
                    max_servers=dynamic_max_servers,
                    rng=rng,
                )

            raw = model.run()
            summary = summarize_run(raw, sla_wait_threshold=sla_wait_threshold)
            summaries.append(summary)

            waits = interval_waiting_times(raw)
            for index, interval in enumerate(raw["interval_metrics"]):
                if len(interval_accumulator) <= index:
                    interval_accumulator.append({
                        "start": interval["start"],
                        "end": interval["end"],
                        "duration": interval["duration"],
                        "utilization": [],
                        "avg_queue_length": [],
                        "servers": [],
                        "lambda": interval["lambda"],
                        "waiting_time": [],
                    })
                bucket = interval_accumulator[index]
                bucket["utilization"].append(interval["utilization"])
                bucket["avg_queue_length"].append(interval["avg_queue_length"])
                bucket["servers"].append(interval["servers"])
                if waits[index] is not None:
                    bucket["waiting_time"].append(waits[index])

            event_counts.append({
                "scale_up": summary["scale_up_events"],
                "scale_down": summary["scale_down_events"],
            })

        avg = {}
        std = {}
        metric_names = [
            "avg_waiting_time",
            "avg_system_time",
            "avg_queue_length",
            "avg_utilization",
            "sla_violations",
            "sla_violation_rate",
            "avg_active_servers",
            "server_hours",
            "scale_up_events",
            "scale_down_events",
        ]
        for metric in metric_names:
            values = [s[metric] for s in summaries]
            avg[metric] = sum(values) / len(values)
            variance = sum((x - avg[metric]) ** 2 for x in values) / (len(values) - 1) if len(values) > 1 else 0.0
            std[metric] = variance ** 0.5

        time_series = []
        for bucket in interval_accumulator:
            time_series.append({
                "start": bucket["start"],
                "end": bucket["end"],
                "time": bucket["end"],
                "lambda": bucket["lambda"],
                "utilization": sum(bucket["utilization"]) / len(bucket["utilization"]),
                "avg_queue_length": sum(bucket["avg_queue_length"]) / len(bucket["avg_queue_length"]),
                "avg_active_servers": sum(bucket["servers"]) / len(bucket["servers"]),
                "avg_waiting_time": (
                    sum(bucket["waiting_time"]) / len(bucket["waiting_time"])
                    if bucket["waiting_time"] else 0.0
                ),
            })

        all_results[key] = {
            "label": config["label"],
            "average": avg,
            "stddev": std,
            "time_series": time_series,
            "configuration": config,
        }

    return {
        "experiment": {
            "horizon": horizon,
            "service_rate": service_rate,
            "repetitions": repetitions,
            "seed": seed,
            "sla_wait_threshold": sla_wait_threshold,
            "workload": workload,
            "control_interval": control_interval,
            "dynamic_policy": {
                "initial_servers": dynamic_initial_servers,
                "min_servers": dynamic_min_servers,
                "max_servers": dynamic_max_servers,
                "low_utilization": low_utilization,
                "high_utilization": high_utilization,
                "queue_high": queue_high,
                "queue_low": queue_low,
                "cooldown": cooldown,
            },
        },
        "results": all_results,
    }


def save_results(result, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["experiment", "avg_waiting_time", "avg_system_time", "avg_queue_length",
                  "avg_utilization", "sla_violations", "sla_violation_rate",
                  "avg_active_servers", "server_hours", "scale_up_events", "scale_down_events"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key, data in result["results"].items():
            row = {"experiment": data["label"]}
            row.update(data["average"])
            writer.writerow(row)

    with (output_dir / "time_series.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["experiment", "time", "lambda", "utilization", "avg_queue_length", "avg_active_servers", "avg_waiting_time"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for key, data in result["results"].items():
            for point in data["time_series"]:
                writer.writerow({"experiment": data["label"], **{field: point[field] for field in fields[1:]}})


def print_summary(result):
    print("\nMonte Carlo autoscaling experiment")
    print("=" * 100)
    print(f"Replications: {result['experiment']['repetitions']}")
    print(f"SLA waiting-time threshold: {result['experiment']['sla_wait_threshold']:.2f}")
    print()
    print(f"{'Metric':<25}{'Static c=2':>18}{'Static c=6':>18}{'Dynamic':>18}")
    print("-" * 80)
    metrics = [
        ("Avg waiting time", "avg_waiting_time"),
        ("Avg system time", "avg_system_time"),
        ("Avg queue length", "avg_queue_length"),
        ("Avg utilization", "avg_utilization"),
        ("SLA violations", "sla_violations"),
        ("SLA violation rate", "sla_violation_rate"),
        ("Avg active servers", "avg_active_servers"),
        ("Server-hours", "server_hours"),
        ("Scale-up events", "scale_up_events"),
        ("Scale-down events", "scale_down_events"),
    ]
    for label, key in metrics:
        values = [result["results"][name]["average"][key] for name in CONFIG]
        print(f"{label:<25}{values[0]:>18.4f}{values[1]:>18.4f}{values[2]:>18.4f}")


def main():
    result = run_experiments()
    output_dir = PROJECT_ROOT / "experiments" / "results"
    save_results(result, output_dir)
    print_summary(result)
    print(f"\nResults written to: {output_dir}")


if __name__ == "__main__":
    main()
