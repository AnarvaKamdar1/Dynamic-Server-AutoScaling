import matplotlib.pyplot as plt


def plot_utilization(
    x_values,
    simulated_values,
    theoretical_values,
    x_label="Arrival rate (lambda)",
    title="Utilization vs Arrival Rate"
):
    """
    Plot simulated and theoretical utilization.

    x_values:
        Values used on the x-axis, e.g. lambda.

    simulated_values:
        Utilization obtained from simulation.

    theoretical_values:
        Theoretical utilization.
    """

    plt.figure(figsize=(8, 5))

    plt.plot(
        x_values,
        simulated_values,
        marker="o",
        label="Simulated"
    )

    plt.plot(
        x_values,
        theoretical_values,
        marker="o",
        linestyle="--",
        label="Theoretical"
    )

    plt.xlabel(x_label)
    plt.ylabel("Utilization")

    plt.title(title)

    plt.grid(True, alpha=0.3)

    plt.legend()

    plt.tight_layout()

    plt.show()


def plot_latency(
    x_values,
    simulated_values,
    theoretical_values,
    x_label="Arrival rate (lambda)",
    title="Latency vs Arrival Rate"
):
    """
    Plot simulated and theoretical latency.

    Here latency means average system time.

    x_values:
        Values used on the x-axis.

    simulated_values:
        Average system time from simulation.

    theoretical_values:
        Theoretical average system time.
    """

    plt.figure(figsize=(8, 5))

    plt.plot(
        x_values,
        simulated_values,
        marker="o",
        label="Simulated"
    )

    plt.plot(
        x_values,
        theoretical_values,
        marker="o",
        linestyle="--",
        label="Theoretical"
    )

    plt.xlabel(x_label)
    plt.ylabel("Average system time")

    plt.title(title)

    plt.grid(True, alpha=0.3)

    plt.legend()

    plt.tight_layout()

    plt.show()