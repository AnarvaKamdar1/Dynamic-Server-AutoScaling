"""Simulation metrics and analytical M/M/1 and M/M/c results."""


def calculate_utilization(results, num_servers=1):
    arrival_times = results["arrival_times"]
    departure_times = results["departure_times"]
    service_times = results["service_times"]

    simulation_start = arrival_times[0]
    simulation_end = departure_times[-1]
    total_busy_time = sum(service_times)
    total_capacity = num_servers * (simulation_end - simulation_start)
    return total_busy_time / total_capacity


def calculate_average_waiting_time(results):
    arrivals = results["arrival_times"]
    starts = results["service_start_times"]
    return sum(start - arrival for arrival, start in zip(arrivals, starts)) / len(arrivals)


def calculate_average_system_time(results):
    arrivals = results["arrival_times"]
    departures = results["departure_times"]
    return sum(departure - arrival for arrival, departure in zip(arrivals, departures)) / len(arrivals)


def _observed_arrival_rate(results):
    arrivals = results["arrival_times"]
    return len(arrivals) / (arrivals[-1] - arrivals[0])


def calculate_average_queue_length(results):
    return _observed_arrival_rate(results) * calculate_average_waiting_time(results)


def calculate_average_system_length(results):
    return _observed_arrival_rate(results) * calculate_average_system_time(results)


def evaluate_simulation(results, num_servers=1):
    return {
        "utilization": calculate_utilization(results, num_servers),
        "avg_queue_length": calculate_average_queue_length(results),
        "avg_system_length": calculate_average_system_length(results),
        "avg_waiting_time": calculate_average_waiting_time(results),
        "avg_system_time": calculate_average_system_time(results),
    }


def evaluate_theoretical_mm1(arrival_rate, service_rate):
    if arrival_rate <= 0 or service_rate <= 0:
        raise ValueError("arrival_rate and service_rate must be > 0")
    if arrival_rate >= service_rate:
        raise ValueError("M/M/1 is unstable when lambda >= mu")

    rho = arrival_rate / service_rate
    avg_queue_length = rho**2 / (1 - rho)
    avg_system_length = rho / (1 - rho)
    avg_waiting_time = avg_queue_length / arrival_rate
    avg_system_time = avg_system_length / arrival_rate

    return {
        "utilization": rho,
        "avg_queue_length": avg_queue_length,
        "avg_system_length": avg_system_length,
        "avg_waiting_time": avg_waiting_time,
        "avg_system_time": avg_system_time,
    }


def evaluate_theoretical_mmc(arrival_rate, service_rate, num_servers):
    if arrival_rate <= 0 or service_rate <= 0 or num_servers <= 0:
        raise ValueError("rates and num_servers must be > 0")

    c = num_servers
    rho = arrival_rate / (c * service_rate)
    if rho >= 1:
        raise ValueError("M/M/c is unstable when lambda >= c * mu")

    traffic_intensity = arrival_rate / service_rate
    p0_sum = sum(traffic_intensity**n / _factorial(n) for n in range(c))
    p0 = 1 / (p0_sum + traffic_intensity**c / (_factorial(c) * (1 - rho)))
    probability_wait = (
        traffic_intensity**c / _factorial(c)
        * p0 / (1 - rho)
    )

    avg_queue_length = probability_wait * rho / (1 - rho)
    avg_waiting_time = avg_queue_length / arrival_rate
    avg_system_time = avg_waiting_time + 1 / service_rate
    avg_system_length = arrival_rate * avg_system_time

    return {
        "utilization": rho,
        "avg_queue_length": avg_queue_length,
        "avg_system_length": avg_system_length,
        "avg_waiting_time": avg_waiting_time,
        "avg_system_time": avg_system_time,
    }


def _factorial(n):
    result = 1
    for value in range(2, n + 1):
        result *= value
    return result


def evaluate_theoretical(arrival_rate, service_rate, num_servers):
    if num_servers == 1:
        return evaluate_theoretical_mm1(arrival_rate, service_rate)
    return evaluate_theoretical_mmc(arrival_rate, service_rate, num_servers)
