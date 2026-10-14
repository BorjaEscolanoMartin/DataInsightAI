import json
from unittest.mock import MagicMock

import pytest

from app.services.insights_check import Dropped
from demo import generate_demo_fixture

KEPT = {"title": "Promoción", "description": "Con promoción, 2.907,93 de media.", "columns": []}
INSIGHTS = {"trends": [KEPT], "anomalies": [], "correlations": [], "recommendations": []}
DROPPED = [Dropped("anomalies", "Pico", ["28,5", "645"])]


@pytest.fixture
def generated(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_demo_fixture.settings, "anthropic_api_key", "sk-test-fake")
    monkeypatch.setattr(generate_demo_fixture, "FIXTURE_DIR", tmp_path)
    mock = MagicMock(return_value=(INSIGHTS, DROPPED))
    monkeypatch.setattr(generate_demo_fixture, "generate_insights_checked", mock)
    return mock


def test_dry_run_prints_the_check_report_and_writes_nothing(generated, tmp_path, capsys):
    generate_demo_fixture.main(["--dry-run", "--model", "claude-sonnet-5-5"])

    assert list(tmp_path.iterdir()) == []
    assert [call.kwargs["model"] for call in generated.call_args_list] == ["claude-sonnet-5-5"] * 2
    report = capsys.readouterr().out.splitlines()
    assert report[:4] == [
        "== demo_ventas_diarias.csv (claude-sonnet-5-5): 1 kept, 1 dropped ==",
        "[trends] Promoción: Con promoción, 2.907,93 de media.",
        "DROPPED [anomalies] Pico: figures not in the data: 28,5, 645",
        "== demo_viviendas.csv (claude-sonnet-5-5): 1 kept, 1 dropped ==",
    ]


def test_a_normal_run_writes_both_fixtures_with_the_default_model(generated, tmp_path):
    generate_demo_fixture.main([])

    assert sorted(p.name for p in tmp_path.iterdir()) == ["ventas.json", "viviendas.json"]
    assert [call.kwargs["model"] for call in generated.call_args_list] == ["claude-opus-5-5"] * 2
    fixture = json.loads((tmp_path / "ventas.json").read_text(encoding="utf-8"))
    assert fixture["analysis"]["insights"] == INSIGHTS


def test_without_a_key_nothing_runs(generated, monkeypatch, tmp_path):
    monkeypatch.setattr(generate_demo_fixture.settings, "anthropic_api_key", "")

    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY is not set"):
        generate_demo_fixture.main(["--dry-run"])

    generated.assert_not_called()
    assert list(tmp_path.iterdir()) == []


OLD_INSIGHTS = {
    "trends": [{"title": "Antiguo", "description": "Texto previo.", "columns": []}],
    "anomalies": [],
    "correlations": [],
    "recommendations": [],
}


def _write_stale_fixtures(directory):
    for name in ("ventas.json", "viviendas.json"):
        stale = {
            "filename": "x.csv",
            "analysis": {"profile": {"stale": True}, "insights": OLD_INSIGHTS},
        }
        (directory / name).write_text(json.dumps(stale), encoding="utf-8")


def test_keep_insights_recomputes_the_rest_without_a_key_or_a_call(
    generated, monkeypatch, tmp_path
):
    from app.services.profiling import profile_csv

    monkeypatch.setattr(generate_demo_fixture.settings, "anthropic_api_key", "")
    _write_stale_fixtures(tmp_path)

    generate_demo_fixture.main(["--keep-insights"])

    generated.assert_not_called()
    for fixture_name, csv_name in generate_demo_fixture.DATASETS.items():
        fixture = json.loads((tmp_path / fixture_name).read_text(encoding="utf-8"))
        content = (generate_demo_fixture.DEMO_DIR / csv_name).read_bytes()
        assert fixture["filename"] == csv_name
        assert fixture["size_bytes"] == len(content)
        assert fixture["analysis"]["profile"] == profile_csv(content)
        assert fixture["analysis"]["insights"] == OLD_INSIGHTS
        assert "predictions" in fixture["analysis"]


def test_keep_insights_needs_the_existing_fixtures(generated, tmp_path):
    (tmp_path / "ventas.json").write_text(
        json.dumps({"analysis": {"insights": OLD_INSIGHTS}}), encoding="utf-8"
    )

    with pytest.raises(SystemExit, match="viviendas.json"):
        generate_demo_fixture.main(["--keep-insights"])

    generated.assert_not_called()
    assert json.loads((tmp_path / "ventas.json").read_text(encoding="utf-8")) == {
        "analysis": {"insights": OLD_INSIGHTS}
    }


def test_keep_insights_and_dry_run_cannot_be_combined(generated, tmp_path):
    _write_stale_fixtures(tmp_path)

    with pytest.raises(SystemExit):
        generate_demo_fixture.main(["--keep-insights", "--dry-run"])

    generated.assert_not_called()
