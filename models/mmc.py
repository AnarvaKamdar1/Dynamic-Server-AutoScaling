import random
from typing import Optional


class MMC:
    """Reusable M/M/c discrete-event simulation model."""

    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
        num_servers: int,
        num_customers: int,
        rng: Optional[random.Random] = None,
    ):
        if arrival_rate <= 0 or service_rate <= 0:
            raise ValueError("arrival_rate and service_rate must be > 0")
        if num_servers <= 0:
            raise ValueError("num_servers must be > 0")
        if num_customers <= 0:
            raise ValueError("num_customers must be > 0")

        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.num_servers = num_servers
        self.num_customers = num_customers
        self.rng = rng or random.Random()

    def run(self):
        arrival_times = []
        service_times = []
        service_start_times = []
        departure_times = []
        server_assignments = []

        current_arrival_time = 0.0
        server_available_times = [0.0] * self.num_servers

        for _ in range(self.num_customers):
            current_arrival_time += self.rng.expovariate(self.arrival_rate)
            service_time = self.rng.expovariate(self.service_rate)

            server = min(
                range(self.num_servers),
                key=server_available_times.__getitem__,
            )

            service_start_time = max(
                current_arrival_time,
                server_available_times[server],
            )
            departure_time = service_start_time + service_time
            server_available_times[server] = departure_time

            arrival_times.append(current_arrival_time)
            service_times.append(service_time)
            service_start_times.append(service_start_time)
            departure_times.append(departure_time)
            server_assignments.append(server)

        return {
            "arrival_times": arrival_times,
            "service_times": service_times,
            "service_start_times": service_start_times,
            "departure_times": departure_times,
            "server_assignments": server_assignments,
        }
