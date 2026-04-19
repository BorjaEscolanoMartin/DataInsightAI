from app.services.report import generate_report


PROFILE = {
    "row_count": 200,
    "column_count": 3,
    "date_column_candidate": "fecha",
    "columns": [
        {
            "name": "ventas",
            "type": "numeric",
            "null_count": 0,
            "null_pct": 0.0,
            "unique_count": 180,
            "mean": 150.0,
            "std": 30.0,
        },
        {
            "name": "categoria",
            "type": "categorical",
            "null_count": 2,
            "null_pct": 1.0,
            "unique_count": 4,
            "top_categories": [{"value": "A", "count": 100}, {"value": "B", "count": 80}],
        },
    ],
}

INSIGHTS = {
    "trends": [{"title": "Tendencia al alza", "description": "Desc.", "columns": ["ventas"]}],
    "anomalies": [],
    "correlations": [],
    "recommendations": [{"title": "Revisar nulos", "description": "Desc.", "columns": []}],
}

PREDICTIONS_FORECAST = {
    "forecast": {
        "target_column": "ventas",
        "date_column": "fecha",
        "mape": 5.3,
        "horizon_days": 30,
        "points": [
            {"ds": "2024-02-01", "yhat": 160.0, "yhat_lower": 140.0, "yhat_upper": 180.0},
            {"ds": "2024-02-02", "yhat": 162.0, "yhat_lower": 138.0, "yhat_upper": 186.0},
        ],
    },
    "regression": None,
}

PREDICTIONS_REGRESSION = {
    "forecast": None,
    "regression": {
        "target_column": "ventas",
        "r2": 0.82,
        "rmse": 12.5,
        "feature_importance": [
            {"feature": "categoria", "importance": 0.65},
            {"feature": "descuento", "importance": 0.35},
        ],
    },
}


def _is_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def test_report_returns_pdf_bytes():
    pdf = generate_report("ventas.csv", PROFILE, None, None)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
    assert _is_pdf(pdf)


def test_report_with_insights():
    pdf = generate_report("ventas.csv", PROFILE, INSIGHTS, None)
    assert _is_pdf(pdf)


def test_report_with_forecast():
    pdf = generate_report("ventas.csv", PROFILE, INSIGHTS, PREDICTIONS_FORECAST)
    assert _is_pdf(pdf)


def test_report_with_regression():
    pdf = generate_report("ventas.csv", PROFILE, INSIGHTS, PREDICTIONS_REGRESSION)
    assert _is_pdf(pdf)


def test_report_without_insights_or_predictions():
    pdf = generate_report("datos.csv", PROFILE, None, None)
    assert _is_pdf(pdf)
