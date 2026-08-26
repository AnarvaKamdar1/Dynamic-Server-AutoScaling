"""Shared metrics for the static-vs-dynamic autoscaling experiments."""


def summarize_run(raw, sla_wait_threshold=1.0):
    customers = raw["customers"]
    completed = [c for c in customers if c["departure_time"] is not None]
    waiting = [c["service_start_time"] - c["arrival_time"] for c in completed]
    system = [c["departure_time"] - c["arrival_time"] for c in completed]

    intervals = raw["interval_metrics"]
    total_duration = sum(x["duration"] for x in intervals) or raw["horizon"]
    avg_utilization = sum(x["utilization"] * x["duration"] for x in intervals) / total_duration
    avg_queue = sum(x["avg_queue_length"] * x["duration"] for x in intervals) / total_duration
    avg_servers = sum(x["servers"] * x["duration"] for x in intervals) / total_duration

    return {
        "arrivals": len(customers),
        "completed": len(completed),
        "unfinished": len(customers) - len(completed),
        "avg_utilization": avg_utilization,
        "avg_queue_length": avg_queue,
        "avg_waiting_time": sum(waiting) / len(waiting) if waiting else 0.0,
        "avg_system_time": sum(system) / len(system) if system else 0.0,
        "sla_violations": sum(w > sla_wait_threshold for w in waiting),
        "sla_violation_rate": (
            sum(w > sla_wait_threshold for w in waiting) / len(waiting) if waiting else 0.0
        ),
        "avg_active_servers": avg_servers,
        "server_hours": avg_servers * raw["horizon"],
        "scale_up_events": sum(e["action"] == "add_server" for e in raw.get("scaling_events", [])),
        "scale_down_events": sum(e["action"] == "remove_server" for e in raw.get("scaling_events", [])),
    }


def interval_waiting_times(raw, bin_count=None):
    """Return average waiting time associated with each recorded interval."""
    intervals = raw["interval_metrics"]
    values = []
    for interval in intervals:
        waits = []
        for customer in raw["customers"]:
            start = customer["service_start_time"]
            if start is None:
                continue
            if interval["start"] <= start < interval["end"] or (
                abs(start - interval["end"]) < 1e-12 and interval["end"] == raw["horizon"]
            ):
                waits.append(start - customer["arrival_time"])
        values.append(sum(waits) / len(waits) if waits else None)
    return values
