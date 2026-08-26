"""Metrics and event summaries for dynamic M/M/c simulations."""

from statistics import mean


def summarize_dynamic_run(raw):
    """Create a compact summary from a dynamic M/M/c simulation result."""
    horizon = raw["horizon"]
    customers = raw["customers"]
    completed = [c for c in customers if c["departure_time"] is not None]

    if horizon <= 0:
        raise ValueError("horizon must be > 0")

    total_wait = sum(c["service_start_time"] - c["arrival_time"] for c in completed)
    total_system = sum(c["departure_time"] - c["arrival_time"] for c in completed)

    interval_metrics = raw["interval_metrics"]
    weighted_utilization = (
        sum(x["utilization"] * x["duration"] for x in interval_metrics)
        / sum(x["duration"] for x in interval_metrics)
        if interval_metrics else 0.0
    )
    avg_queue = (
        sum(x["avg_queue_length"] * x["duration"] for x in interval_metrics)
        / sum(x["duration"] for x in interval_metrics)
        if interval_metrics else 0.0
    )

    return {
        "horizon": horizon,
        "arrivals": len(customers),
        "completed": len(completed),
        "unfinished": len(customers) - len(completed),
        "avg_utilization": weighted_utilization,
        "avg_queue_length": avg_queue,
        "avg_waiting_time": total_wait / len(completed) if completed else 0.0,
        "avg_system_time": total_system / len(completed) if completed else 0.0,
        "initial_servers": raw["initial_servers"],
        "final_servers": raw["final_servers"],
        "scale_up_events": sum(e["action"] == "add_server" for e in raw["scaling_events"]),
        "scale_down_events": sum(e["action"] == "remove_server" for e in raw["scaling_events"]),
        "scaling_events": raw["scaling_events"],
        "scaling_policy": raw.get("scaling_policy", {}),
    }


def print_dynamic_summary(summary):
    """Print the run summary and the scaling decisions."""
    print("\nDynamic M/M/c summary")
    print("=" * 72)
    print(f"Horizon:             {summary['horizon']:.2f}")
    print(f"Arrivals:            {summary['arrivals']}")
    print(f"Completed:           {summary['completed']}")
    print(f"Average utilization: {summary['avg_utilization']:.4f}")
    print(f"Average queue:       {summary['avg_queue_length']:.4f}")
    print(f"Average waiting:     {summary['avg_waiting_time']:.4f}")
    print(f"Average system time: {summary['avg_system_time']:.4f}")
    print(f"Servers:             {summary['initial_servers']} -> {summary['final_servers']}")
    print(f"Scale up events:     {summary['scale_up_events']}")
    print(f"Scale down events:   {summary['scale_down_events']}")
    policy = summary.get("scaling_policy")
    if policy:
        print(f"Queue-up threshold:   {policy['queue_high']:.2f}")
        print(f"Queue-down threshold: {policy['queue_low']:.2f}")
        print(f"Cooldown:             {policy['cooldown']:.2f}")

    print("\nScaling decisions")
    print("-" * 72)
    if not summary["scaling_events"]:
        print("No scaling decisions were triggered.")
        return

    for event in summary["scaling_events"]:
        print(
            f"t={event['time']:8.2f} | {event['action']:<13} | "
            f"servers={event['servers_before']}->{event['servers_after']} | "
            f"utilization={event['utilization']:.3f} | "
            f"lambda={event['lambda']:.3f} | queue={event['queue_length']} | "
            f"{event['reason']}"
        )
