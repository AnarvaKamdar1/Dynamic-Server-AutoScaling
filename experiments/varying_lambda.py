import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "experiments" else Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

"""Parameter sweep with fixed mu and varying lambda."""

from analysis.plot import plot_utilization, plot_latency
from experiments.common import run_parameter_sweep


def run_varying_lambda(
    model,
    service_rate,
    lambda_values,
    num_customers,
    num_servers=1,
    seed=None,
    plot=True,
):
    rows = run_parameter_sweep(
        model,
        lambda_values,
        varying="lambda",
        fixed_rate=service_rate,
        num_customers=num_customers,
        num_servers=num_servers,
        seed=seed,
    )

    if plot and rows:
        x = [row["lambda"] for row in rows]
        plot_utilization(
            x,
            [row["sim_utilization"] for row in rows],
            [row["theory_utilization"] for row in rows],
            x_label="Arrival rate (lambda)",
            title=f"{model.upper().replace('MMC', 'M/M/c')} Utilization vs Arrival Rate",
        )
        plot_latency(
            x,
            [row["sim_avg_system_time"] for row in rows],
            [row["theory_avg_system_time"] for row in rows],
            x_label="Arrival rate (lambda)",
            title=f"{model.upper().replace('MMC', 'M/M/c')} Latency vs Arrival Rate",
        )
    return rows


def main():
    MODEL = "mmc"
    NUM_SERVERS = 4
    NUM_CUSTOMERS = 10_000
    MU = 10.0
    LAMBDA_VALUES = range(1, 10)

    run_varying_lambda(
        model=MODEL,
        service_rate=MU,
        lambda_values=LAMBDA_VALUES,
        num_customers=NUM_CUSTOMERS,
        num_servers=NUM_SERVERS,
    )


if __name__ == "__main__":
    main()
