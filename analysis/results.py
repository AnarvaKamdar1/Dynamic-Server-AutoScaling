from analysis.evaluate import (
    evaluate_simulation,
    evaluate_theoretical
)


def print_results(
    model_name,
    arrival_rate,
    service_rate,
    num_customers,
    num_servers,
    simulation_results
):
    """
    Evaluate and print simulation results.
    """

    # --------------------------------------------------
    # Calculate simulated metrics
    # --------------------------------------------------

    simulated = evaluate_simulation(
        simulation_results,
        num_servers
    )

    # --------------------------------------------------
    # Calculate theoretical metrics
    # --------------------------------------------------

    theoretical = evaluate_theoretical(
        arrival_rate,
        service_rate,
        num_servers
    )

    # --------------------------------------------------
    # Print experiment information
    # --------------------------------------------------

    print()
    print(model_name)
    print("=" * len(model_name))

    print(
        f"Arrival rate (lambda): {arrival_rate}"
    )

    print(
        f"Service rate (mu):     {service_rate}"
    )

    print(
        f"Servers (c):           {num_servers}"
    )

    print(
        f"Customers:             {num_customers}"
    )

    # --------------------------------------------------
    # Print metrics
    # --------------------------------------------------

    print()

    print(
        f"{'Metric':<25}"
        f"{'Simulated':>15}"
        f"{'Theoretical':>15}"
    )

    print("-" * 55)

    metrics = [
        ("Utilization", "utilization"),
        ("Average queue length", "avg_queue_length"),
        ("Average system length", "avg_system_length"),
        ("Average waiting time", "avg_waiting_time"),
        ("Average system time", "avg_system_time"),
    ]

    for name, key in metrics:

        print(
            f"{name:<25}"
            f"{simulated[key]:>15.6f}"
            f"{theoretical[key]:>15.6f}"
        )