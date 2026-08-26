import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "experiments" else Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

"""Parameter sweep with fixed lambda and varying mu."""

from analysis.plot import plot_utilization, plot_latency
from experiments.common import run_parameter_sweep


def run_varying_mu(
    model,
    arrival_rate,
    mu_values,
    num_customers,
    num_servers=1,
    seed=None,
    plot=True,
):
    rows = run_parameter_sweep(
        model,
        mu_values,
        varying="mu",
        fixed_rate=arrival_rate,
        num_customers=num_customers,
        num_servers=num_servers,
        seed=seed,
    )

    if plot and rows:
        x = [row["mu"] for row in rows]
        plot_utilization(
            x,
            [row["sim_utilization"] for row in rows],
            [row["theory_utilization"] for row in rows],
            x_label="Service rate (mu)",
            title=f"{model.upper()} Utilization vs Service Rate",
        )
        plot_latency(
            x,
            [row["sim_avg_system_time"] for row in rows],
            [row["theory_avg_system_time"] for row in rows],
            x_label="Service rate (mu)",
            title=f"{model.upper()} Latency vs Service Rate",
        )
    return rows


def main():
    MODEL = "mm1"
    NUM_SERVERS = 1
    NUM_CUSTOMERS = 10_000
    LAMBDA = 5.0
    MU_VALUES = range(6, 16)

    run_varying_mu(
        model=MODEL,
        arrival_rate=LAMBDA,
        mu_values=MU_VALUES,
        num_customers=NUM_CUSTOMERS,
        num_servers=NUM_SERVERS,
    )


if __name__ == "__main__":
    main()
