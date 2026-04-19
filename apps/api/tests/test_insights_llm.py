from unittest.mock import MagicMock, patch
from app.services.insights_llm import generate_insights, _build_prompt


SAMPLE_PROFILE = {
    "row_count": 100,
    "column_count": 3,
    "date_column_candidate": "fecha",
    "charts": [],
    "columns": [
        {
            "name": "ventas",
            "type": "numeric",
            "null_pct": 0.0,
            "null_count": 0,
            "unique_count": 80,
            "mean": 150.0,
            "std": 30.0,
            "min_val": 50.0,
            "max_val": 300.0,
            "outlier_count": 3,
        },
        {
            "name": "categoria",
            "type": "categorical",
            "null_pct": 2.0,
            "null_count": 2,
            "unique_count": 4,
            "top_categories": [
                {"value": "A", "count": 40},
                {"value": "B", "count": 35},
            ],
        },
    ],
}

VALID_RESPONSE = """{
  "trends": [{"title": "Ventas crecientes", "description": "Las ventas muestran tendencia al alza.", "columns": ["ventas"]}],
  "anomalies": [{"title": "Outliers en ventas", "description": "Se detectaron 3 outliers por IQR.", "columns": ["ventas"]}],
  "correlations": [],
  "recommendations": [{"title": "Revisar categoría A", "description": "La categoría A domina con 40%.", "columns": ["categoria"]}]
}"""


def test_build_prompt_contains_columns():
    prompt = _build_prompt(SAMPLE_PROFILE)
    assert "ventas" in prompt
    assert "categoria" in prompt
    assert "100 filas" in prompt


def test_build_prompt_includes_date_candidate():
    prompt = _build_prompt(SAMPLE_PROFILE)
    assert "fecha" in prompt


def test_generate_insights_returns_empty_without_api_key():
    with patch("app.services.insights_llm.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        result = generate_insights(SAMPLE_PROFILE)
    assert result["trends"] == []
    assert result["anomalies"] == []
    assert result["correlations"] == []
    assert result["recommendations"] == []


def test_generate_insights_parses_valid_json():
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=VALID_RESPONSE)]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.insights_llm.settings") as mock_settings, \
         patch("app.services.insights_llm.Anthropic", return_value=mock_client):
        mock_settings.anthropic_api_key = "sk-test-fake"
        result = generate_insights(SAMPLE_PROFILE)

    assert len(result["trends"]) == 1
    assert result["trends"][0]["title"] == "Ventas crecientes"
    assert len(result["anomalies"]) == 1
    assert result["correlations"] == []
    assert len(result["recommendations"]) == 1


def test_generate_insights_strips_markdown_fences():
    fenced = f"```json\n{VALID_RESPONSE}\n```"
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=fenced)]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.services.insights_llm.settings") as mock_settings, \
         patch("app.services.insights_llm.Anthropic", return_value=mock_client):
        mock_settings.anthropic_api_key = "sk-test-fake"
        result = generate_insights(SAMPLE_PROFILE)

    assert result["trends"][0]["title"] == "Ventas crecientes"
