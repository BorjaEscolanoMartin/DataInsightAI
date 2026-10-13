from unittest.mock import MagicMock

import pytest

from app.services import forecasting, ml_baseline
from app.workers.tasks import _run_predictions

CONTENT = b"csv bytes"


def _profile(columns: dict[str, str], date_column: str | None = None) -> dict:
    return {
        "date_column_candidate": date_column,
        "columns": [{"name": name, "type": kind} for name, kind in columns.items()],
    }


@pytest.fixture
def forecast(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(return_value={"points": [{"ds": "2024-03-01", "yhat": 1.0}]})
    monkeypatch.setattr(forecasting, "run_forecast", mock)
    return mock


@pytest.fixture
def regression(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock = MagicMock(return_value={"target_column": "precio", "r2": 0.9})
    monkeypatch.setattr(ml_baseline, "run_regression", mock)
    return mock


def test_without_numeric_columns_there_is_no_prediction(forecast, regression):
    profile = _profile({"fecha": "datetime", "region": "categorical"}, date_column="fecha")

    assert _run_predictions(CONTENT, profile) is None
    forecast.assert_not_called()
    regression.assert_not_called()


def test_with_a_date_column_the_first_numeric_column_is_forecast(forecast, regression):
    profile = _profile(
        {"fecha": "datetime", "ventas": "numeric", "unidades": "numeric"}, date_column="fecha"
    )

    result = _run_predictions(CONTENT, profile)

    assert result == {"forecast": forecast.return_value, "regression": None}
    forecast.assert_called_once_with(CONTENT, "fecha", "ventas", horizon_days=30)
    regression.assert_not_called()


def test_without_a_date_column_the_last_numeric_column_is_regressed(forecast, regression):
    profile = _profile(
        {"superficie": "numeric", "habitaciones": "numeric", "zona": "categorical",
         "precio": "numeric"}
    )

    result = _run_predictions(CONTENT, profile)

    assert result == {"forecast": None, "regression": regression.return_value}
    regression.assert_called_once_with(CONTENT, "precio", ["superficie", "habitaciones", "zona"])
    forecast.assert_not_called()
