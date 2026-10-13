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
