import json
from typing import Any
from anthropic import Anthropic
from app.config import settings
from app.schemas.insights import InsightsOut

SYSTEM_PROMPT = """\
Eres un analista de datos experto. Analiza el perfil estadístico de un dataset y genera insights accionables.

Responde ÚNICAMENTE con JSON válido con esta estructura exacta (sin markdown, sin texto extra):
{
  "trends":         [{"title": "...", "description": "...", "columns": ["col"]}],
  "anomalies":      [{"title": "...", "description": "...", "columns": ["col"]}],
  "correlations":   [{"title": "...", "description": "...", "columns": ["col1","col2"]}],
  "recommendations":[{"title": "...", "description": "...", "columns": []}]
}

Reglas:
- 2-4 items por categoría; array vacío si no hay nada relevante.
- title: máximo 8 palabras.
- description: 2-3 frases específicas con valores concretos del perfil.
- columns: nombres exactos de las columnas mencionadas.
- Responde todo en español.\
"""


def _build_prompt(profile: dict[str, Any]) -> str:
    lines: list[str] = [
        f"Dataset: {profile.get('row_count', '?')} filas × {profile.get('column_count', '?')} columnas",
        "",
        "Columnas:",
    ]

    for col in profile.get("columns", []):
        name = col["name"]
        col_type = col["type"]
        null_pct = col.get("null_pct", 0)
        unique = col.get("unique_count", 0)
        desc = f"  {name} ({col_type}) — {null_pct}% nulos, {unique} únicos"

        if col_type == "numeric":
            mean = col.get("mean")
            std = col.get("std")
            min_v = col.get("min_val")
            max_v = col.get("max_val")
            outliers = col.get("outlier_count", 0)
            if mean is not None:
                desc += f" | media={mean:.3g}, std={std:.3g}, min={min_v:.3g}, max={max_v:.3g}"
            if outliers:
                desc += f" | {outliers} outliers (IQR)"
        elif col_type in ("categorical", "boolean"):
            top = col.get("top_categories", [])[:4]
            if top:
                cats = ", ".join(f"{c['value']}({c['count']})" for c in top)
                desc += f" | top: {cats}"

        lines.append(desc)

    date_cand = profile.get("date_column_candidate")
    if date_cand:
        lines.append(f"\nColumna de fecha: {date_cand}")

    # Correlaciones altas desde el heatmap
    charts = profile.get("charts", [])
    heatmap = next((c for c in charts if c["type"] == "heatmap"), None)
    if heatmap:
        seen: set[tuple[str, str]] = set()
        high: list[str] = []
        for d in heatmap.get("data", []):
            if d["x"] == d["y"]:
                continue
            if abs(d["value"]) < 0.6:
                continue
            key = tuple(sorted([d["x"], d["y"]]))
            if key in seen:
                continue
            seen.add(key)
            high.append(f"  {d['x']} ↔ {d['y']}: r={d['value']:.3f}")
        if high:
            lines.append("\nCorrelaciones destacadas (|r|>0.6):")
            lines.extend(high[:6])

    lines.append("\nGenera los insights:")
    return "\n".join(lines)


def generate_insights(profile: dict[str, Any]) -> dict[str, Any]:
    if not settings.anthropic_api_key:
        return InsightsOut().model_dump()

    client = Anthropic(api_key=settings.anthropic_api_key, max_retries=3)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(profile)}],
    )

    raw = message.content[0].text.strip()

    # Strip accidental markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)
    return InsightsOut.model_validate(data).model_dump()
