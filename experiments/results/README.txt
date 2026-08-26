Existing single-workload experiment results are retained for reference.

New policy/workload study:
    python experiments/policy_workload_experiments.py
    python experiments/plot_policy_study.py

The policy study writes to:
    experiments/results/policy_study/

The default study is 100 matched Monte Carlo replications for every workload /
policy combination and three systems (static c=2, static c=6, selected dynamic policy).

Static baselines are policy-independent, so the implementation simulates each
static baseline once per workload and reuses those matched results for every policy.
This is computationally equivalent to repeating them for every policy while avoiding
unnecessary duplicate simulation.
