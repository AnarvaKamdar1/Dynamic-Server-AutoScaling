"""Create time-series comparison plots from compare_autoscaling.py output.

Run from the project root:
    python experiments/plot_experiment_results.py
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = PROJECT_ROOT / "experiments" / "results"


def load_time_series(path):
    rows = []
    with path.open("r", newline="", encoding="utf-8") as f:
        rows.extend(csv.DictReader(f))
    return rows


def plot_metric(rows, metric, ylabel, title, filename):
    labels = {
        "Static c=2": [],
        "Static c=6": [],
        "Dynamic autoscaling": [],
    }
    for label in labels:
        selected = [r for r in rows if r["experiment"] == label]
        labels[label] = (
            [float(r["time"]) for r in selected],
            [float(r[metric]) for r in selected],
        )

    plt.figure(figsize=(9, 5))
    for label, (x, y) in labels.items():
        plt.plot(x, y, marker="o", markersize=3, label=label)
    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULT_DIR / filename, dpi=160)
    plt.close()


def main():
    rows = load_time_series(RESULT_DIR / "time_series.csv")
    plot_metric(rows, "utilization", "Utilization", "Utilization vs Time", "utilization_vs_time.png")
    plot_metric(rows, "avg_queue_length", "Average queue length", "Average Queue Length vs Time", "queue_vs_time.png")
    plot_metric(rows, "avg_active_servers", "Active servers", "Active Servers vs Time", "servers_vs_time.png")
    plot_metric(rows, "avg_waiting_time", "Average waiting time", "Average Waiting Time vs Time", "waiting_vs_time.png")
    print(f"Plots written to: {RESULT_DIR}")


if __name__ == "__main__":
    main()
