# Autoscaling policy and workload study

## Research design

For every combination of workload pattern and autoscaling policy, run the same
100 Monte Carlo seeds for three systems:

1. Static M/M/c with `c=2` (under-provisioned baseline)
2. Static M/M/c with `c=6` (over-provisioned baseline)
3. Dynamic M/M/c using the selected autoscaling policy

The same arrival/service random seed is reused across the three systems within
each replication so the comparison is paired/fair.

## Workloads

- `step_spike`: 2 -> 8 -> 18 -> 5 -> 2
- `gradual_ramp`: 2 -> 4 -> 6 -> 8 -> 10
- `sudden_spike`: 2 -> 18 -> 2
- `repeated_spikes`: 2 -> 15 -> 3 -> 18 -> 2
- `bursty`: frequent alternating low/moderate/high load

## Policies

- `balanced`: 0.80 high utilization / 20 queue / 0.30 low utilization / 20 cooldown
- `aggressive`: 0.70 / 10 / 0.25 / 10 cooldown
- `conservative`: 0.90 / 30 / 0.20 / 30 cooldown
- `queue_priority`: 0.90 / 10 / 0.35 / 15 cooldown
- `fast_response`: 0.75 / 15 / 0.25 / 5 cooldown

For scale-down, utilization must be below the low threshold **and** the average
queue must be at or below the low queue threshold. Only an idle server is removed.

## Metrics

- Average waiting time
- Average system time
- Average queue length
- Average utilization
- SLA violation count/rate
- Average active servers
- Server-hours
- Scale-up and scale-down events

The default SLA is waiting time > 1.0 time unit.

## Commands

From the project root:

```powershell
python experiments/policy_workload_experiments.py
python experiments/plot_policy_study.py
```

Results are written to `experiments/results/policy_study/`.
