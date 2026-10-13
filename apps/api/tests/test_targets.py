from app.services.targets import forecast_target, regression_target


def _profile(columns: dict[str, str], identifiers: tuple[str, ...] = ()) -> dict:
    return {
        "columns": [
            {"name": name, "type": kind, "is_identifier": name in identifiers}
            for name, kind in columns.items()
        ]
    }


def test_forecast_target_is_the_first_numeric_column_that_is_not_an_identifier():
    profile = _profile(
        {"fecha": "date", "Id. de la fila": "numeric", "ventas": "numeric", "pedidos": "numeric"},
        identifiers=("Id. de la fila",),
    )

    assert forecast_target(profile) == "ventas"


def test_forecast_target_is_none_with_only_identifiers():
    profile = _profile({"fecha": "date", "id": "numeric"}, identifiers=("id",))

    assert forecast_target(profile) is None


def test_regression_target_is_the_last_numeric_column_when_there_are_two():
    profile = _profile({"metros": "numeric", "zona": "categorical", "precio": "numeric"})

    assert regression_target(profile) == "precio"


def test_regression_target_is_none_with_a_single_numeric_column():
    profile = _profile({"zona": "categorical", "precio": "numeric"})

    assert regression_target(profile) is None
