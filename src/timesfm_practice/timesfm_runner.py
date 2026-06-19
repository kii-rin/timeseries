from __future__ import annotations

import numpy as np


def forecast_with_timesfm(history: np.ndarray, horizon: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Run TimesFM 2.5 if installed.

    Install first with: pip install timesfm[torch]
    """
    try:
        import torch
        import timesfm
    except ImportError as exc:
        raise RuntimeError(
            "TimesFM is not installed. Run `pip install timesfm[torch]` first."
        ) from exc

    torch.set_float32_matmul_precision("high")
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        "google/timesfm-2.5-200m-pytorch"
    )
    model.compile(
        timesfm.ForecastConfig(
            max_context=max(1024, len(history)),
            max_horizon=max(256, horizon),
            normalize_inputs=True,
            use_continuous_quantile_head=True,
            force_flip_invariance=True,
            infer_is_positive=False,
            fix_quantile_crossing=True,
        )
    )
    point_forecast, quantile_forecast = model.forecast(
        horizon=horizon,
        inputs=[np.asarray(history, dtype=float)],
    )
    return point_forecast[0], quantile_forecast[0]
