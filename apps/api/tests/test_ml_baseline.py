import numpy as np
import pandas as pd

from app.services.ml_baseline import run_regression


def _csv(rows: int) -> bytes:
    # Fixed seed: precio follows superficie; ruido has no relation with it.
    rng = np.random.default_rng(0)
    superficie = np.linspace(40, 200, rows)
    frame = pd.DataFrame(
        {
            "superficie": superficie,
            "ruido": rng.uniform(0, 100, rows),
            "precio": 2 * superficie + rng.normal(0, 5, rows),
        }
    )
    return frame.to_csv(index=False).encode()


def test_regression_reports_fit_metrics_and_ranked_importances():
    result = run_regression(_csv(60), "precio", ["superficie", "ruido"])

    assert set(result) == {"target_column", "r2", "rmse", "feature_importance"}
    assert result["target_column"] == "precio"
    assert result["r2"] > 0.8
    assert result["rmse"] > 0
    importances = [item["importance"] for item in result["feature_importance"]]
    assert [item["feature"] for item in result["feature_importance"]] == ["superficie", "ruido"]
    assert importances == sorted(importances, reverse=True)


def test_regression_with_fewer_than_twenty_rows_returns_empty_metrics():
    result = run_regression(_csv(19), "precio", ["superficie", "ruido"])

    assert result == {"target_column": "precio", "r2": 0.0, "rmse": 0.0, "feature_importance": []}
