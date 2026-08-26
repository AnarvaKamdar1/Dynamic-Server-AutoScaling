"""Reusable dynamic workload patterns for autoscaling experiments."""

WORKLOAD_PATTERNS = {
    "step_spike": {
        "label": "Step spike",
        "description": "Low load, moderate load, sharp high-load phase, then recovery.",
        "segments": [
            (0, 50, 2.0),
            (50, 100, 8.0),
            (100, 150, 18.0),
            (150, 200, 5.0),
            (200, 250, 2.0),
        ],
    },
    "gradual_ramp": {
        "label": "Gradual ramp",
        "description": "Arrival rate increases in stages and then remains high.",
        "segments": [
            (0, 50, 2.0),
            (50, 100, 4.0),
            (100, 150, 6.0),
            (150, 200, 8.0),
            (200, 250, 10.0),
        ],
    },
    "sudden_spike": {
        "label": "Sudden spike",
        "description": "Long low-load period, one abrupt spike, then recovery.",
        "segments": [
            (0, 75, 2.0),
            (75, 125, 18.0),
            (125, 250, 2.0),
        ],
    },
    "repeated_spikes": {
        "label": "Repeated spikes",
        "description": "Two separated high-load bursts.",
        "segments": [
            (0, 50, 2.0),
            (50, 90, 15.0),
            (90, 130, 3.0),
            (130, 175, 18.0),
            (175, 250, 2.0),
        ],
    },
    "bursty": {
        "label": "Bursty workload",
        "description": "Frequent alternating moderate/high and low-load periods.",
        "segments": [
            (0, 30, 2.0),
            (30, 55, 12.0),
            (55, 80, 3.0),
            (80, 110, 15.0),
            (110, 140, 4.0),
            (140, 170, 14.0),
            (170, 200, 3.0),
            (200, 225, 10.0),
            (225, 250, 2.0),
        ],
    },
}
