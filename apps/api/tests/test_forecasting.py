import math
from datetime import date, timedelta

from app.services.forecasting import run_forecast

START = date(2024, 1, 1)
DAYS = 60
WEEKLY = [0, 5, 10, 8, 3, -4, -6]


def _daily_csv() -> bytes:
    rows = ["fecha,ventas"]
    for i in range(DAYS):
        rows.append(f"{START + timedelta(days=i)},{100 + 2 * i + WEEKLY[i % 7]}")
    return ("\n".join(rows) + "\n").encode()


def test_forecast_returns_points_for_each_day_of_the_horizon():
    result = run_forecast(_daily_csv(), "fecha", "ventas", horizon_days=30)

    last = START + timedelta(days=DAYS - 1)
    expected_days = [str(last + timedelta(days=i)) for i in range(1, 31)]
    assert [p["ds"] for p in result["points"]] == expected_days
    for p in result["points"]:
        assert math.isfinite(p["yhat"])
        assert p["yhat_lower"] <= p["yhat"] <= p["yhat_upper"]
    assert isinstance(result["mape"], float)
    assert result["horizon_days"] == 30
