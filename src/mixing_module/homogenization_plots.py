from __future__ import annotations

import pandas as pd

from .homogenization_metrics import HomogenizationPoint


def metrics_dataframe(series: list[HomogenizationPoint]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "time_s": p.time_s,
                "sigma2": p.sigma2,
                "rsd_percent": p.rsd_percent,
                "lacey_index": p.lacey_index,
                "h_rel": p.h_rel,
                "sigma0_2": p.sigma0_2,
                "sigma_r_eff_2": p.sigma_r_eff_2,
            }
            for p in series
        ]
    )


def concentration_profile_dataframe(cells: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"cell": [f"Cell {i+1}" for i in range(len(cells))], "concentration": cells})


def component_contribution_dataframe(contribs: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"component": [f"Component {i+1}" for i in range(len(contribs))], "contribution": contribs}
    )
