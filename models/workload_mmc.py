"""Fixed-server M/M/c simulation under a piecewise-constant workload."""

import heapq
import random
from collections import deque
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple


@dataclass(frozen=True)
class WorkloadSegment:
    start: float
    end: float
    arrival_rate: float


class WorkloadMMC:
    """Event-driven M/M/c simulation with a time-varying arrival rate."""

    def __init__(
        self,
        service_rate: float,
        horizon: float,
        num_servers: int,
        workload: Sequence[Tuple[float, float, float]],
        control_interval: float = 10.0,
        rng: Optional[random.Random] = None,
    ):
        if service_rate <= 0 or horizon <= 0 or num_servers <= 0:
            raise ValueError("service_rate, horizon and num_servers must be > 0")
        if control_interval <= 0:
            raise ValueError("control_interval must be > 0")
        self.service_rate = service_rate
        self.horizon = horizon
        self.num_servers = num_servers
        self.control_interval = control_interval
        self.rng = rng or random.Random()
        self.workload = self._validate_workload(workload)

    def _validate_workload(self, workload):
        segments = [WorkloadSegment(*segment) for segment in workload]
        if not segments:
            raise ValueError("workload must contain at least one segment")
        previous_end = 0.0
        for segment in segments:
            if segment.start < 0 or segment.end <= segment.start:
                raise ValueError("workload segments must have 0 <= start < end")
            if abs(segment.start - previous_end) > 1e-12:
                raise ValueError("workload segments must be contiguous starting at 0")
            if segment.arrival_rate < 0:
                raise ValueError("arrival_rate must be >= 0")
            previous_end = segment.end
        if previous_end < self.horizon:
            raise ValueError("workload must cover the complete simulation horizon")
        return segments

    def _arrival_rate_at(self, time):
        for segment in self.workload:
            if segment.start <= time < segment.end:
                return segment.arrival_rate
        return 0.0

    def _next_boundary(self, time):
        for segment in self.workload:
            if segment.start > time:
                return min(segment.start, self.horizon)
        return self.horizon

    def _new_arrival(self, time):
        rate = self._arrival_rate_at(time)
        if rate <= 0:
            return float("inf")
        return time + self.rng.expovariate(rate)

    def run(self):
        servers = [None] * self.num_servers
        queue = deque()
        customers = []
        completions = []
        interval_metrics = []

        time = 0.0
        next_arrival = self._new_arrival(0.0)
        next_boundary = self._next_boundary(0.0)
        next_control = min(self.control_interval, self.horizon)
        interval_start = 0.0
        last_time = 0.0
        busy_area = 0.0
        queue_area = 0.0
        next_customer_id = 0

        def busy_count():
            return sum(value is not None for value in servers)

        def integrate(until):
            nonlocal last_time, busy_area, queue_area
            dt = max(0.0, until - last_time)
            busy_area += busy_count() * dt
            queue_area += len(queue) * dt
            last_time = until

        def start_customer(customer_id, server_id, now):
            service_time = self.rng.expovariate(self.service_rate)
            departure = now + service_time
            servers[server_id] = departure
            heapq.heappush(completions, (departure, server_id, customer_id))
            customers[customer_id]["service_start_time"] = now
            customers[customer_id]["service_time"] = service_time
            customers[customer_id]["server_id"] = server_id

        def assign_waiting(now):
            while queue:
                idle = next((i for i, value in enumerate(servers) if value is None), None)
                if idle is None:
                    return
                customer_id = queue.popleft()
                start_customer(customer_id, idle, now)

        def complete_due(now):
            while completions and completions[0][0] <= now + 1e-12:
                departure, server_id, customer_id = heapq.heappop(completions)
                servers[server_id] = None
                customers[customer_id]["departure_time"] = departure
                assign_waiting(now)

        while time < self.horizon - 1e-12:
            next_completion = completions[0][0] if completions else float("inf")
            event_time = min(next_arrival, next_completion, next_boundary, next_control, self.horizon)
            integrate(event_time)
            time = event_time

            if time >= next_boundary - 1e-12:
                next_arrival = self._new_arrival(time)
                next_boundary = self._next_boundary(time)

            complete_due(time)

            if next_arrival <= time + 1e-12 and next_arrival < self.horizon + 1e-12:
                customer = {
                    "id": next_customer_id,
                    "arrival_time": time,
                    "service_start_time": None,
                    "service_time": None,
                    "departure_time": None,
                    "server_id": None,
                }
                customers.append(customer)
                idle = next((i for i, value in enumerate(servers) if value is None), None)
                if idle is None:
                    queue.append(next_customer_id)
                else:
                    start_customer(next_customer_id, idle, time)
                next_customer_id += 1
                next_arrival = self._new_arrival(time)

            if time >= next_control - 1e-12:
                duration = max(time - interval_start, 1e-12)
                interval_metrics.append({
                    "start": interval_start,
                    "end": time,
                    "duration": duration,
                    "utilization": busy_area / (duration * self.num_servers),
                    "avg_queue_length": queue_area / duration,
                    "servers": self.num_servers,
                    "lambda": self._arrival_rate_at(max(interval_start, time - 1e-9)),
                })
                interval_start = time
                busy_area = 0.0
                queue_area = 0.0
                next_control = min(next_control + self.control_interval, self.horizon)

        integrate(self.horizon)
        complete_due(self.horizon)

        return {
            "horizon": self.horizon,
            "service_rate": self.service_rate,
            "initial_servers": self.num_servers,
            "final_servers": self.num_servers,
            "workload": [segment.__dict__.copy() for segment in self.workload],
            "customers": customers,
            "scaling_events": [],
            "interval_metrics": interval_metrics,
        }
