"""Monte Carlo experiment matrix for autoscaling policies and workloads.

For every (workload, policy) pair, the experiment runs 100 matched Monte Carlo
replications of:
    A. Static c=2
    B. Static c=6
    C. Dynamic autoscaling using the selected policy

Run from the project root:
    python experiments/policy_workload_experiments.py

Outputs are written to experiments/results/policy_study/.
"""

import csv
import json
import math
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.experiment_metrics import interval_waiting_times, summarize_run
from models.autoscaling_policies import POLICIES, get_policy
from models.dynamic_mmc import DynamicMMC
from models.workload_mmc import WorkloadMMC
from experiments.workload_patterns import WORKLOAD_PATTERNS

SYSTEMS = {
    "static_c2": {"label": "Static c=2", "type": "static", "servers": 2},
    "static_c6": {"label": "Static c=6", "type": "static", "servers": 6},
}

METRICS = [
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


def mean(values):
    return sum(values) / len(values) if values else 0.0


def stddev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def ci95(values):
    if not values:
        return 0.0
    return 1.96 * stddev(values) / math.sqrt(len(values))


def make_model(system_key, workload, rng, *, service_rate, horizon, control_interval,
               policy_name, dynamic_initial_servers=2, dynamic_min_servers=1,
               dynamic_max_servers=10):
    if system_key == "static_c2":
        return WorkloadMMC(service_rate, horizon, 2, workload, control_interval, rng)
    if system_key == "static_c6":
        return WorkloadMMC(service_rate, horizon, 6, workload, control_interval, rng)
    policy = get_policy(policy_name)
    return DynamicMMC(
        service_rate=service_rate,
        horizon=horizon,
        initial_servers=dynamic_initial_servers,
        workload=workload,
        control_interval=control_interval,
        low_utilization=policy.low_utilization,
        high_utilization=policy.high_utilization,
        queue_high=policy.queue_high,
        queue_low=policy.queue_low,
        cooldown=policy.cooldown,
        min_servers=dynamic_min_servers,
        max_servers=dynamic_max_servers,
        rng=rng,
        policy=policy,
    )


def run_study(*, repetitions=100, seed=42, service_rate=5.0, horizon=250.0,
              control_interval=10.0, sla_wait_threshold=1.0):
    master_rng = random.Random(seed)
    workload_seeds = {
        name: [master_rng.randrange(2**63) for _ in range(repetitions)]
        for name in WORKLOAD_PATTERNS
    }

    combination_rows = []
    time_series_rows = []

    # Static baselines do not depend on the autoscaling policy, so simulate them
    # once per workload and reuse those matched Monte Carlo results for every policy.
    static_cache = {}

    def simulate_system(system_key, workload, run_seed, policy_name):
        rng = random.Random(run_seed)
        model = make_model(
            system_key, workload, rng,
            service_rate=service_rate,
            horizon=horizon,
            control_interval=control_interval,
            policy_name=policy_name,
        )
        raw = model.run()
        return raw, summarize_run(raw, sla_wait_threshold=sla_wait_threshold)

    def aggregate_intervals(raws):
        buckets = []
        for raw in raws:
            waits = interval_waiting_times(raw)
            for i, interval in enumerate(raw["interval_metrics"]):
                if len(buckets) <= i:
                    buckets.append({
                        "start": interval["start"], "end": interval["end"],
                        "duration": interval["duration"], "lambda": interval["lambda"],
                        "utilization": [], "avg_queue_length": [],
                        "avg_active_servers": [], "avg_waiting_time": [],
                    })
                b = buckets[i]
                b["utilization"].append(interval["utilization"])
                b["avg_queue_length"].append(interval["avg_queue_length"])
                b["avg_active_servers"].append(interval["servers"])
                if waits[i] is not None:
                    b["avg_waiting_time"].append(waits[i])
        return [
            {
                "start": b["start"], "end": b["end"], "time": b["end"],
                "lambda": b["lambda"],
                "utilization": mean(b["utilization"]),
                "avg_queue_length": mean(b["avg_queue_length"]),
                "avg_active_servers": mean(b["avg_active_servers"]),
                "avg_waiting_time": mean(b["avg_waiting_time"]),
            }
            for b in buckets
        ]

    def add_results(workload_name, workload_info, policy_name, system_key, summaries, ts):
        system_label = SYSTEMS.get(system_key, {"label": ""})["label"] if system_key != "dynamic" else f"Dynamic - {POLICIES[policy_name].label}"
        for metric in METRICS:
            vals = [s[metric] for s in summaries]
            combination_rows.append({
                "workload": workload_name,
                "workload_label": workload_info["label"],
                "policy": policy_name,
                "policy_label": POLICIES[policy_name].label,
                "system": system_key,
                "system_label": system_label,
                "metric": metric,
                "mean": mean(vals),
                "stddev": stddev(vals),
                "ci95": ci95(vals),
                "repetitions": len(vals),
            })
        for point in ts:
            time_series_rows.append({
                "workload": workload_name,
                "workload_label": workload_info["label"],
                "policy": policy_name,
                "policy_label": POLICIES[policy_name].label,
                "system": system_key,
                "system_label": system_label,
                **{k: point[k] for k in ("time", "lambda", "utilization", "avg_queue_length", "avg_active_servers", "avg_waiting_time")},
            })

    for workload_name, workload_info in WORKLOAD_PATTERNS.items():
        workload = workload_info["segments"]
        seeds = workload_seeds[workload_name]

        # Build the two static baselines once.
        for system_key in ("static_c2", "static_c6"):
            summaries = []
            raws = []
            for run_seed in seeds:
                raw, summary = simulate_system(system_key, workload, run_seed, "balanced")
                raws.append(raw)
                summaries.append(summary)
            static_cache[(workload_name, system_key)] = (summaries, aggregate_intervals(raws))

        # Every policy gets the same seeds and the same static baselines.
        for policy_name in POLICIES:
            for system_key in ("static_c2", "static_c6"):
                summaries, ts = static_cache[(workload_name, system_key)]
                add_results(workload_name, workload_info, policy_name, system_key, summaries, ts)

            dynamic_summaries = []
            dynamic_raws = []
            for run_seed in seeds:
                raw, summary = simulate_system("dynamic", workload, run_seed, policy_name)
                dynamic_raws.append(raw)
                dynamic_summaries.append(summary)
            add_results(workload_name, workload_info, policy_name, "dynamic", dynamic_summaries, aggregate_intervals(dynamic_raws))

    result = {
        "configuration": {
            "repetitions": repetitions,
            "seed": seed,
            "service_rate": service_rate,
            "horizon": horizon,
            "control_interval": control_interval,
            "sla_wait_threshold": sla_wait_threshold,
            "static_systems": {k: v["servers"] for k, v in SYSTEMS.items()},
            "policies": {k: v.as_dict() for k, v in POLICIES.items()},
            "workloads": WORKLOAD_PATTERNS,
            "methodology": "Matched random seeds; static baselines reused across policies because they are policy-independent.",
        },
        "combination_results": combination_rows,
        "time_series": time_series_rows,
    }
    result["policy_ranking"] = build_policy_ranking(result)
    return result


def build_policy_ranking(result):
    """Create a transparent cross-workload ranking for dynamic policies.

    The score is the equal-weight mean of min-max normalized waiting time,
    system time, queue length, SLA violation rate, and server-hours. Lower is
    better. The score is a decision aid, not a claim that one policy is
    universally optimal; Pareto dominance is also reported.
    """
    rows = result["combination_results"]
    metrics = ["avg_waiting_time", "avg_system_time", "avg_queue_length", "sla_violation_rate", "server_hours"]
    dynamic = [r for r in rows if r["system"] == "dynamic" and r["metric"] in metrics]
    values = {}
    for policy in POLICIES:
        values[policy] = {}
        for metric in metrics:
            vals = [r["mean"] for r in dynamic if r["policy"] == policy and r["metric"] == metric]
            values[policy][metric] = mean(vals)

    normalized = {p: {} for p in POLICIES}
    for metric in metrics:
        vals = [values[p][metric] for p in POLICIES]
        lo, hi = min(vals), max(vals)
        for p in POLICIES:
            normalized[p][metric] = 0.0 if hi == lo else (values[p][metric] - lo) / (hi - lo)

    # All objectives are costs here; lower is better.
    result_rows = []
    for p in POLICIES:
        score = mean(list(normalized[p].values()))
        result_rows.append({
            "policy": p,
            "policy_label": POLICIES[p].label,
            **values[p],
            "balanced_score": score,
        })

    # Pareto-optimal policies: no other policy is <= on every metric and < on at least one.
    for row in result_rows:
        p = row["policy"]
        dominated = False
        for other in result_rows:
            if other["policy"] == p:
                continue
            no_worse = all(other[m] <= row[m] + 1e-12 for m in metrics)
            strictly_better = any(other[m] < row[m] - 1e-12 for m in metrics)
            if no_worse and strictly_better:
                dominated = True
                break
        row["pareto_optimal"] = not dominated

    result_rows.sort(key=lambda r: r["balanced_score"])
    for i, row in enumerate(result_rows, 1):
        row["rank"] = i
    return result_rows

def save_study(result, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "study_config.json").open("w", encoding="utf-8") as f:
        json.dump(result["configuration"], f, indent=2)

    fields = list(result["combination_results"][0].keys())
    with (output_dir / "combination_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["combination_results"])

    fields = list(result["time_series"][0].keys())
    with (output_dir / "time_series.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["time_series"])

    # A compact table for the most important metrics in each workload/policy/system combination.
    key_metrics = ["avg_waiting_time", "avg_system_time", "avg_queue_length", "sla_violation_rate", "avg_active_servers", "server_hours"]
    lookup = {(r["workload"], r["policy"], r["system"], r["metric"]): r["mean"] for r in result["combination_results"]}
    rows = []
    for w in WORKLOAD_PATTERNS:
        for p in POLICIES:
            for s in ["static_c2", "static_c6", "dynamic"]:
                row = {"workload": w, "policy": p, "system": s}
                for m in key_metrics:
                    row[m] = lookup[(w, p, s, m)]
                rows.append(row)
    fields = list(rows[0].keys())
    with (output_dir / "summary_by_combination.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    ranking_fields = list(result["policy_ranking"][0].keys())
    with (output_dir / "policy_ranking.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ranking_fields)
        writer.writeheader()
        writer.writerows(result["policy_ranking"])

    with (output_dir / "policy_ranking.json").open("w", encoding="utf-8") as f:
        json.dump(result["policy_ranking"], f, indent=2)

    return output_dir


def print_progress_summary(result):
    rows = result["combination_results"]
    # Only print the main metrics for dynamic policies to keep console output manageable.
    key = {r["metric"]: r["mean"] for r in rows if r["workload"] == "step_spike" and r["policy"] == "balanced" and r["system"] == "dynamic"}
    print("\nPolicy/workload Monte Carlo study")
    print("=" * 78)
    print(f"Replications per system/policy/workload: {result['configuration']['repetitions']}")
    print(f"Workload patterns: {len(WORKLOAD_PATTERNS)}")
    print(f"Autoscaling policies: {len(POLICIES)}")
    print("\nExample (step spike + balanced dynamic policy):")
    print(f"  Avg waiting time: {key['avg_waiting_time']:.4f}")
    print(f"  SLA violation rate: {key['sla_violation_rate']:.4%}")
    print(f"  Avg active servers: {key['avg_active_servers']:.4f}")
    print("\nCross-workload policy ranking (lower balanced score is better):")
    for row in result["policy_ranking"]:
        marker = "*" if row["pareto_optimal"] else " "
        print(f" {marker} {row['rank']}. {row['policy_label']:<16} score={row['balanced_score']:.4f}")


def main():
    result = run_study()
    out = PROJECT_ROOT / "experiments" / "results" / "policy_study"
    save_study(result, out)
    print_progress_summary(result)
    print(f"\nResults written to: {out}")


if __name__ == "__main__":
    main()
