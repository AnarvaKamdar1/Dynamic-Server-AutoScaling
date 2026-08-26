This directory is populated by:

python experiments/policy_workload_experiments.py
python experiments/plot_policy_study.py

Files:
- combination_results.csv: mean, standard deviation and 95% CI for each metric,
  workload, policy and system.
- summary_by_combination.csv: compact comparison table.
- time_series.csv: Monte Carlo-average time-series metrics.
- policy_ranking.csv/json: cross-workload policy ranking and Pareto-optimal flag.
- plots/: time-series charts.
