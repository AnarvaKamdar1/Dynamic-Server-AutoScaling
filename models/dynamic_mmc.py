"""Dynamic M/M/c simulator with workload changes and autoscaling.

The workload is a piecewise-constant arrival-rate schedule. The service rate
is per server. At each control interval, the simulator measures utilization
and can add/remove one server while keeping the current queue and jobs alive.
"""

import heapq
import random
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from models.autoscaling_policies import AutoscalingPolicy


@dataclass(frozen=True)
class WorkloadSegment:
    start: float
    end: float
    arrival_rate: float


class DynamicMMC:
    """Event-driven dynamic M/M/c simulation with simple autoscaling."""

    def __init__(
        self,
        service_rate: float,
        horizon: float,
        initial_servers: int,
        workload: Sequence[Tuple[float, float, float]],
        control_interval: float = 10.0,
        low_utilization: float = 0.30,
        high_utilization: float = 0.80,
        queue_high: float = 20.0,
        queue_low: float = 0.0,
        cooldown: float = 20.0,
        min_servers: int = 1,
        max_servers: int = 20,
        rng: Optional[random.Random] = None,
        policy: Optional[AutoscalingPolicy] = None,
    ):
        if service_rate <= 0:
            raise ValueError("service_rate must be > 0")
        if horizon <= 0:
            raise ValueError("horizon must be > 0")
        if initial_servers <= 0:
            raise ValueError("initial_servers must be > 0")
        if control_interval <= 0:
            raise ValueError("control_interval must be > 0")
        if not 0 <= low_utilization < high_utilization:
            raise ValueError("require 0 <= low_utilization < high_utilization")
        if queue_high < queue_low or queue_low < 0:
            raise ValueError("require 0 <= queue_low <= queue_high")
        if cooldown < 0:
            raise ValueError("cooldown must be >= 0")
        if min_servers <= 0 or max_servers < min_servers:
            raise ValueError("invalid server bounds")
        if not min_servers <= initial_servers <= max_servers:
            raise ValueError("initial_servers must be within server bounds")

        self.service_rate = service_rate
        self.horizon = horizon
        self.initial_servers = initial_servers
        self.control_interval = control_interval
        self.low_utilization = low_utilization
        self.high_utilization = high_utilization
        self.queue_high = queue_high
        self.queue_low = queue_low
        self.cooldown = cooldown
        self.min_servers = min_servers
        self.max_servers = max_servers
        self.rng = rng or random.Random()
        self.policy = policy or AutoscalingPolicy(
            name="custom",
            label="Custom",
            low_utilization=low_utilization,
            high_utilization=high_utilization,
            queue_high=queue_high,
            queue_low=queue_low,
            cooldown=cooldown,
        )
        self.low_utilization = self.policy.low_utilization
        self.high_utilization = self.policy.high_utilization
        self.queue_high = self.policy.queue_high
        self.queue_low = self.policy.queue_low
        self.cooldown = self.policy.cooldown
        self.workload = self._validate_workload(workload)

    def _validate_workload(self, workload):
        segments = [WorkloadSegment(*segment) for segment in workload]
        if not segments:
            raise ValueError("workload must contain at least one segment")

        previous_end = 0.0
        for segment in segments:
            if segment.start < 0 or segment.end <= segment.start:
                raise ValueError("workload segments must have 0 <= start < end")
            if segment.start != previous_end:
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

    def _next_workload_boundary(self, time):
        for segment in self.workload:
            if segment.start > time:
                return min(segment.start, self.horizon)
        return self.horizon

    def _new_arrival(self, time):
        rate = self._arrival_rate_at(time)
        if rate <= 0:
            return float("inf")
        return time + self.rng.expovariate(rate)

    def _service_time(self):
        return self.rng.expovariate(self.service_rate)

    def run(self):
        # Each server stores its current customer's departure time, or None.
        server_busy_until = [None] * self.initial_servers
        queue = deque()
        customers = []
        completion_events = []  # (departure_time, server_id, customer_id)
        scaling_events = []
        interval_metrics = []

        time = 0.0
        next_arrival = self._new_arrival(0.0)
        next_boundary = self._next_workload_boundary(0.0)
        next_control = min(self.control_interval, self.horizon)
        interval_start = 0.0
        interval_busy_area = 0.0
        interval_queue_area = 0.0
        last_time = 0.0
        next_customer_id = 0
        last_scale_time = float("-inf")

        def active_servers():
            return len(server_busy_until)

        def busy_count():
            return sum(x is not None for x in server_busy_until)

        def integrate(until):
            nonlocal last_time, interval_busy_area, interval_queue_area
            dt = max(0.0, until - last_time)
            interval_busy_area += busy_count() * dt
            interval_queue_area += len(queue) * dt
            last_time = until

        def start_customer(customer_id, server_id, now):
            service_start = now
            service_time = self._service_time()
            departure = now + service_time
            server_busy_until[server_id] = departure
            heapq.heappush(completion_events, (departure, server_id, customer_id))
            customers[customer_id]["service_start_time"] = service_start
            customers[customer_id]["service_time"] = service_time
            customers[customer_id]["server_id"] = server_id

        def assign_waiting(now):
            while queue:
                idle = next((i for i, value in enumerate(server_busy_until) if value is None), None)
                if idle is None:
                    return
                customer_id = queue.popleft()
                start_customer(customer_id, idle, now)

        def complete_due(now):
            while completion_events and completion_events[0][0] <= now + 1e-12:
                departure, server_id, customer_id = heapq.heappop(completion_events)
                server_busy_until[server_id] = None
                customers[customer_id]["departure_time"] = departure
                assign_waiting(now)

        while time < self.horizon - 1e-12:
            next_completion = completion_events[0][0] if completion_events else float("inf")
            event_time = min(next_arrival, next_completion, next_boundary, next_control, self.horizon)
            integrate(event_time)
            time = event_time

            # Workload change.
            if time >= next_boundary - 1e-12:
                next_arrival = self._new_arrival(time)
                next_boundary = self._next_workload_boundary(time)

            # Service completions before accepting an arrival at the same instant.
            complete_due(time)

            # Arrival.
            if next_arrival <= time + 1e-12 and next_arrival < self.horizon + 1e-12:
                arrival_rate = self._arrival_rate_at(time)
                customer = {
                    "id": next_customer_id,
                    "arrival_time": time,
                    "service_start_time": None,
                    "service_time": None,
                    "departure_time": None,
                    "server_id": None,
                }
                customers.append(customer)
                if any(value is None for value in server_busy_until):
                    idle = next(i for i, value in enumerate(server_busy_until) if value is None)
                    start_customer(next_customer_id, idle, time)
                else:
                    queue.append(next_customer_id)
                next_customer_id += 1
                next_arrival = self._new_arrival(time)

            # Autoscaling decision.
            if time >= next_control - 1e-12:
                duration = max(time - interval_start, 1e-12)
                utilization = interval_busy_area / (duration * active_servers())
                avg_queue = interval_queue_area / duration
                interval_metrics.append({
                    "start": interval_start,
                    "end": time,
                    "duration": duration,
                    "utilization": utilization,
                    "avg_queue_length": avg_queue,
                    "servers": active_servers(),
                    "lambda": self._arrival_rate_at(max(interval_start, time - 1e-9)),
                })

                before = active_servers()
                action = None
                reason = None
                cooldown_active = (time - last_scale_time) < self.cooldown

                # Scale up when either the servers are heavily utilized or the
                # average queue in the just-finished control interval is large.
                scale_up_util = utilization >= self.high_utilization
                scale_up_queue = avg_queue >= self.queue_high

                # Scale down only when both signals indicate spare capacity.
                # Requiring a small/empty queue avoids removing capacity while
                # customers are still waiting.
                scale_down_util = utilization <= self.low_utilization
                scale_down_queue = avg_queue <= self.queue_low

                if not cooldown_active and before < self.max_servers and (scale_up_util or scale_up_queue):
                    server_busy_until.append(None)
                    action = "add_server"
                    triggers = []
                    if scale_up_util:
                        triggers.append(
                            f"utilization {utilization:.3f} >= high threshold {self.high_utilization:.3f}"
                        )
                    if scale_up_queue:
                        triggers.append(
                            f"avg queue {avg_queue:.3f} >= high threshold {self.queue_high:.3f}"
                        )
                    reason = " OR ".join(triggers)
                    assign_waiting(time)
                elif (
                    not cooldown_active
                    and before > self.min_servers
                    and scale_down_util
                    and scale_down_queue
                ):
                    # Only remove an idle server. If all servers are busy, the
                    # next control interval can try again without disrupting work.
                    if server_busy_until and server_busy_until[-1] is None:
                        server_busy_until.pop()
                        action = "remove_server"
                        reason = (
                            f"utilization {utilization:.3f} <= low threshold "
                            f"{self.low_utilization:.3f} AND avg queue {avg_queue:.3f} "
                            f"<= low threshold {self.queue_low:.3f}"
                        )

                if action:
                    last_scale_time = time
                    scaling_events.append({
                        "time": time,
                        "action": action,
                        "servers_before": before,
                        "servers_after": active_servers(),
                        "utilization": utilization,
                        "lambda": self._arrival_rate_at(max(time - 1e-9, 0.0)),
                        "queue_length": len(queue),
                        "reason": reason,
                    })

                interval_start = time
                interval_busy_area = 0.0
                interval_queue_area = 0.0
                next_control = min(next_control + self.control_interval, self.horizon)

        # Finish jobs already in service only if they departed before horizon.
        integrate(self.horizon)
        complete_due(self.horizon)

        return {
            "horizon": self.horizon,
            "service_rate": self.service_rate,
            "initial_servers": self.initial_servers,
            "scaling_policy": {
                "name": self.policy.name,
                "label": self.policy.label,
                "low_utilization": self.low_utilization,
                "high_utilization": self.high_utilization,
                "queue_high": self.queue_high,
                "queue_low": self.queue_low,
                "cooldown": self.cooldown,
            },
            "final_servers": len(server_busy_until),
            "workload": [segment.__dict__.copy() for segment in self.workload],
            "customers": customers,
            "scaling_events": scaling_events,
            "interval_metrics": interval_metrics,
        }
