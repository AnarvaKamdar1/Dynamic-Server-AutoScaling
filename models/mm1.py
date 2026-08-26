import random
from typing import Optional


class MM1:
    """Reusable M/M/1 discrete-event simulation model."""

    num_servers = 1

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        num_customers: int,
        num_servers : int = 1,
        rng: Optional[random.Random] = None,
    ):
        if arrival_rate <= 0 or service_rate <= 0:
            raise ValueError("arrival_rate and service_rate must be > 0")
        if num_customers <= 0:
            raise ValueError("num_customers must be > 0")

        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.num_customers = num_customers
        self.rng = rng or random.Random()

    def run(self):
        arrival_times = []
        service_times = []
        service_start_times = []
        departure_times = []

        current_arrival_time = 0.0
        server_available_time = 0.0

        for _ in range(self.num_customers):
            current_arrival_time += self.rng.expovariate(self.arrival_rate)
            service_time = self.rng.expovariate(self.service_rate)
            service_start_time = max(current_arrival_time, server_available_time)
            departure_time = service_start_time + service_time
            server_available_time = departure_time

            arrival_times.append(current_arrival_time)
            service_times.append(service_time)
            service_start_times.append(service_start_time)
            departure_times.append(departure_time)

        return {
            "arrival_times": arrival_times,
            "service_times": service_times,
            "service_start_times": service_start_times,
            "departure_times": departure_times,
        }
