"""Reusable experiment helpers shared by parameter-sweep scripts."""

import random

from analysis.evaluate import evaluate_simulation, evaluate_theoretical
from models import create_model


METRICS = (
    "utilization",
    "avg_queue_length",
    "avg_system_length",
    "avg_waiting_time",
    "avg_system_time",
)


def run_once(model, arrival_rate, service_rate, num_customers, num_servers=1, seed=None):
    rng = random.Random(seed) if seed is not None else None
    simulation = create_model(
        model,
        arrival_rate=arrival_rate,
        service_rate=service_rate,
        num_customers=num_customers,
        num_servers=num_servers,
        rng=rng,
    )
    raw_results = simulation.run()
    simulated = evaluate_simulation(raw_results, num_servers=num_servers)
    theoretical = evaluate_theoretical(arrival_rate, service_rate, num_servers)
    return {"simulation": simulated, "theoretical": theoretical, "raw": raw_results}


def run_parameter_sweep(
    model,
    parameter_values,
    *,
    varying="lambda",
    fixed_rate,
    num_customers,
    num_servers=1,
    seed=None,
):
    """Run a model over lambda or mu values and return structured results."""
    if varying not in {"lambda", "mu"}:
        raise ValueError("varying must be 'lambda' or 'mu'")

    master_rng = random.Random(seed) if seed is not None else None
    rows = []

    for value in parameter_values:
        arrival_rate = value if varying == "lambda" else fixed_rate
        service_rate = fixed_rate if varying == "lambda" else value

        capacity = num_servers * service_rate
        if arrival_rate >= capacity:
            print(
                f"Skipping lambda={arrival_rate}, mu={service_rate}: "
                "unstable system."
            )
            continue

        run_seed = master_rng.randrange(2**63) if master_rng else None
        result = run_once(
            model,
            arrival_rate,
            service_rate,
            num_customers,
            num_servers,
            run_seed,
        )

        row = {
            "model": model if isinstance(model, str) else model.__name__,
            "lambda": arrival_rate,
            "mu": service_rate,
            "num_servers": num_servers,
            "num_customers": num_customers,
        }
        row.update({f"sim_{k}": result["simulation"][k] for k in METRICS})
        row.update({f"theory_{k}": result["theoretical"][k] for k in METRICS})
        rows.append(row)

    return rows
