from .mm1 import MM1
from .mmc import MMC
from .dynamic_mmc import DynamicMMC
from .workload_mmc import WorkloadMMC
from .autoscaling_policies import AutoscalingPolicy, POLICIES, get_policy


def create_model(model_name, **kwargs):
    if model_name == "mm1":
        return MM1(**kwargs)
    if model_name == "mmc":
        return MMC(**kwargs)
    if model_name == "dynamic_mmc":
        return DynamicMMC(**kwargs)
    if model_name == "workload_mmc":
        return WorkloadMMC(**kwargs)
    raise ValueError(f"Unknown model: {model_name}")
