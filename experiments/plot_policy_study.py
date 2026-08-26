"""Plot Monte Carlo-average time series for the policy/workload study.

Run from the project root:
    python experiments/plot_policy_study.py

For each workload and metric, one figure is produced. Static c=2 and c=6
are shown once, while each autoscaling policy gets its own dynamic line.
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "experiments" / "results" / "policy_study"


def load_rows():
    with (RESULT_DIR / "time_series.csv").open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_rows()
    out = RESULT_DIR / "plots"
    out.mkdir(parents=True, exist_ok=True)

    workloads = sorted({r["workload"] for r in rows})
    policies = sorted({r["policy"] for r in rows})
    metrics = {
        "utilization": "Utilization",
        "avg_queue_length": "Average queue length",
        "avg_active_servers": "Active servers",
        "avg_waiting_time": "Average waiting time",
    }

    # 1) For each workload, compare all policies and both static baselines.
    all_policy_dir = out / "all_policies_by_workload"
    all_policy_dir.mkdir(parents=True, exist_ok=True)
    for workload in workloads:
        selected = [r for r in rows if r["workload"] == workload]
        for metric, ylabel in metrics.items():
            plt.figure(figsize=(11, 5.5))
            for system in ("static_c2", "static_c6"):
                data = [r for r in selected if r["system"] == system]
                if data:
                    plt.plot([float(r["time"]) for r in data], [float(r[metric]) for r in data], marker="o", markersize=2.5, label=data[0]["system_label"])
            for policy in policies:
                data = [r for r in selected if r["system"] == "dynamic" and r["policy"] == policy]
                if data:
                    plt.plot([float(r["time"]) for r in data], [float(r[metric]) for r in data], marker="o", markersize=2.5, label=f"Dynamic - {data[0]['policy_label']}")
            plt.xlabel("Time")
            plt.ylabel(ylabel)
            plt.title(f"{ylabel} vs Time — {selected[0]['workload_label']} — All Policies")
            plt.grid(True, alpha=0.3)
            plt.legend(fontsize=8)
            plt.tight_layout()
            plt.savefig(all_policy_dir / f"{workload}_{metric}.png", dpi=160)
            plt.close()

    # 2) For each policy/workload pair, compare exactly the three systems.
    three_system_dir = out / "three_system_comparisons"
    three_system_dir.mkdir(parents=True, exist_ok=True)
    for workload in workloads:
        workload_dir = three_system_dir / workload
        workload_dir.mkdir(parents=True, exist_ok=True)
        for policy in policies:
            policy_dir = workload_dir / policy
            policy_dir.mkdir(parents=True, exist_ok=True)
            selected = [r for r in rows if r["workload"] == workload and r["policy"] == policy]
            for metric, ylabel in metrics.items():
                plt.figure(figsize=(10, 5.5))
                for system in ("static_c2", "static_c6", "dynamic"):
                    data = [r for r in selected if r["system"] == system]
                    if data:
                        plt.plot([float(r["time"]) for r in data], [float(r[metric]) for r in data], marker="o", markersize=2.5, label=data[0]["system_label"])
                plt.xlabel("Time")
                plt.ylabel(ylabel)
                plt.title(f"{ylabel} vs Time — {selected[0]['workload_label']} — {selected[0]['policy_label']}")
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()
                plt.savefig(policy_dir / f"{metric}.png", dpi=160)
                plt.close()

    print(f"Plots written to: {out}")


if __name__ == "__main__":
    main()
