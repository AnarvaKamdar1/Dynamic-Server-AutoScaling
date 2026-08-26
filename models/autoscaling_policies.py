"""Reusable threshold-based autoscaling policies for the dynamic M/M/c simulator."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AutoscalingPolicy:
    """Threshold policy used by :class:`DynamicMMC`."""

    name: str
    label: str
    low_utilization: float
    high_utilization: float
    queue_high: float
    queue_low: float = 0.0
    cooldown: float = 20.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "name": self.name,
            "label": self.label,
            "low_utilization": self.low_utilization,
            "high_utilization": self.high_utilization,
            "queue_high": self.queue_high,
            "queue_low": self.queue_low,
            "cooldown": self.cooldown,
        }


# These are deliberately different controller behaviors rather than arbitrary
# model variants. They let us study responsiveness versus resource conservation.
POLICIES = {
    "balanced": AutoscalingPolicy(
        name="balanced",
        label="Balanced",
        low_utilization=0.30,
        high_utilization=0.80,
        queue_high=20.0,
        queue_low=0.0,
        cooldown=20.0,
    ),
    "aggressive": AutoscalingPolicy(
        name="aggressive",
        label="Aggressive",
        low_utilization=0.25,
        high_utilization=0.70,
        queue_high=10.0,
        queue_low=0.0,
        cooldown=10.0,
    ),
    "conservative": AutoscalingPolicy(
        name="conservative",
        label="Conservative",
        low_utilization=0.20,
        high_utilization=0.90,
        queue_high=30.0,
        queue_low=0.0,
        cooldown=30.0,
    ),
    "queue_priority": AutoscalingPolicy(
        name="queue_priority",
        label="Queue-priority",
        low_utilization=0.35,
        high_utilization=0.90,
        queue_high=10.0,
        queue_low=0.0,
        cooldown=15.0,
    ),
    "fast_response": AutoscalingPolicy(
        name="fast_response",
        label="Fast-response",
        low_utilization=0.25,
        high_utilization=0.75,
        queue_high=15.0,
        queue_low=0.0,
        cooldown=5.0,
    ),
}


def get_policy(name: str) -> AutoscalingPolicy:
    try:
        return POLICIES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown autoscaling policy: {name}. Available: {list(POLICIES)}") from exc
