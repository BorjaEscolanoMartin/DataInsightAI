from unittest.mock import MagicMock

import pytest

from app.db.models import Analysis
from app.services import forecasting, insights_llm, ml_baseline
from app.workers import tasks
from app.workers.tasks import _run_predictions
from tests.conftest import USER_A

CONTENT = b"csv bytes"


def _profile(
    columns: dict[str, str], date_column: str | None = None, identifiers: tuple[str, ...] = ()
) -> dict:
    return {
        "date_column_candidate": date_column,
        "columns": [
            {"name": name, "type": kind, "is_identifier": name in identifiers}
            for name, kind in columns.items()
        ],
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
    forecast.assert_called_once_with(CONTENT, "fecha", "ventas")
    regression.assert_not_called()


def test_the_forecast_target_skips_identifier_columns(forecast, regression):
    profile = _profile(
        {"fecha": "datetime", "Id. de la fila": "numeric", "ventas": "numeric"},
        date_column="fecha",
        identifiers=("Id. de la fila",),
    )

    result = _run_predictions(CONTENT, profile)

    assert result == {"forecast": forecast.return_value, "regression": None}
    forecast.assert_called_once_with(CONTENT, "fecha", "ventas")


def test_with_only_identifier_columns_there_is_no_forecast(forecast, regression):
    profile = _profile(
        {"fecha": "datetime", "Id. de la fila": "numeric"},
        date_column="fecha",
        identifiers=("Id. de la fila",),
    )

    assert _run_predictions(CONTENT, profile) is None
    forecast.assert_not_called()
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


def test_analysis_downloads_the_storage_path_saved_with_the_dataset(
    db_session, make_dataset, monkeypatch
):
    # Datasets uploaded before the path change keep their old path in storage_path.
    _, dataset, analysis = make_dataset(USER_A)
    legacy_path = f"{USER_A}/legacy/{dataset.id}/ventas de enero.csv"
    dataset.storage_path = legacy_path
    db_session.flush()
    analysis_id = analysis.id
    download = MagicMock(return_value=b"fecha,ventas\n2024-01-01,100\n2024-01-02,120\n")
    monkeypatch.setattr(tasks, "download_file", download)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(insights_llm, "generate_insights", MagicMock(return_value={}))

    # run_analysis closes the session it gets, which detaches the objects loaded above.
    tasks.run_analysis(str(analysis_id))

    download.assert_called_once_with(legacy_path)
    stored = db_session.get(Analysis, analysis_id)
    assert stored is not None and stored.status == "completed"
