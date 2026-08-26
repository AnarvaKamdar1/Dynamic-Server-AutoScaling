import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "experiments" else Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.results import print_results
from models import create_model


def run_single(model, arrival_rate, service_rate, num_customers, num_servers=1, seed=None):
    """Run any supported model once and return its raw simulation results."""
    simulation = create_model(
        model,
        arrival_rate=arrival_rate,
        service_rate=service_rate,
        num_customers=num_customers,
        num_servers=num_servers,
    )
    return simulation.run()


def main():
    arrival_rate = 4.0
    service_rate = 5.0
    num_customers = 10_000
    c_values = [2, 3, 5, 8]

    mm1_results = run_single("mm1", arrival_rate, service_rate, num_customers, 1)
    print_results("Experiment 1: M/M/1", arrival_rate, service_rate, num_customers, 1, mm1_results)

    for experiment_number, c in enumerate(c_values, start=2):
        mmc_results = run_single("mmc", arrival_rate, service_rate, num_customers, c)
        print_results(
            f"Experiment {experiment_number}: M/M/{c}",
            arrival_rate,
            service_rate,
            num_customers,
            c,
            mmc_results,
        )


if __name__ == "__main__":
    main()
