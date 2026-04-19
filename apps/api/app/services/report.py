from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import-untyped]
from reportlab.lib.units import cm  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER  # type: ignore[import-untyped]


# ── Colour palette ────────────────────────────────────────────────────────────
_BG       = colors.HexColor("#0f172a")
_SURFACE  = colors.HexColor("#1e293b")
_BORDER   = colors.HexColor("#334155")
_INDIGO   = colors.HexColor("#6366f1")
_TEXT     = colors.HexColor("#e2e8f0")
_MUTED    = colors.HexColor("#94a3b8")
_AMBER    = colors.HexColor("#f59e0b")
_GREEN    = colors.HexColor("#22c55e")
_BLUE     = colors.HexColor("#60a5fa")
_PURPLE   = colors.HexColor("#a78bfa")
_WHITE    = colors.white


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Normal"],
            fontSize=22,
            textColor=_WHITE,
            spaceAfter=10,
            leading=28,
            fontName="Helvetica-Bold",
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=_MUTED,
            spaceAfter=2,
            fontName="Helvetica",
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Normal"],
            fontSize=13,
            textColor=_INDIGO,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9,
            textColor=_TEXT,
            spaceAfter=4,
            fontName="Helvetica",
            leading=14,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontSize=8,
            textColor=_MUTED,
            fontName="Helvetica",
            leading=12,
        ),
        "insight_title": ParagraphStyle(
            "insight_title",
            parent=base["Normal"],
            fontSize=9,
            textColor=_WHITE,
            fontName="Helvetica-Bold",
            spaceAfter=2,
            leading=13,
        ),
        "insight_body": ParagraphStyle(
            "insight_body",
            parent=base["Normal"],
            fontSize=8,
            textColor=_MUTED,
            fontName="Helvetica",
            leading=12,
        ),
    }


def _hr(width: float = 17 * cm) -> HRFlowable:
    return HRFlowable(width=width, thickness=1, color=_BORDER, spaceAfter=8)


def _stat_table(stats: list[tuple[str, str]], styles: dict) -> Table:
    data = [[Paragraph(f"<b>{v}</b>", styles["body"]), Paragraph(k, styles["small"])]
            for k, v in stats]
    t = Table(data, colWidths=[5 * cm] * len(stats) if len(stats) <= 4 else None,
              hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _SURFACE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_SURFACE]),
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, _BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _columns_table(columns: list[dict], styles: dict) -> Table:
    header = [
        Paragraph("Columna", styles["small"]),
        Paragraph("Tipo", styles["small"]),
        Paragraph("Nulos %", styles["small"]),
        Paragraph("Únicos", styles["small"]),
        Paragraph("Resumen", styles["small"]),
    ]
    rows = [header]
    for col in columns[:30]:
        summary = ""
        if col["type"] == "numeric":
            mean = col.get("mean")
            std = col.get("std")
            if mean is not None:
                summary = f"μ {mean:.2f}  σ {std:.2f}" if std is not None else f"μ {mean:.2f}"
        elif col.get("top_categories"):
            summary = ", ".join(c["value"] for c in col["top_categories"][:3])
        rows.append([
            Paragraph(col["name"], styles["body"]),
            Paragraph(col["type"], styles["small"]),
            Paragraph(f"{col['null_pct']:.1f}%", styles["small"]),
            Paragraph(str(col["unique_count"]), styles["small"]),
            Paragraph(summary[:60], styles["small"]),
        ])

    t = Table(rows, colWidths=[4.5 * cm, 2.5 * cm, 2 * cm, 2 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_SURFACE, _BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, _BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


_CATEGORY_LABEL = {
    "trends": ("↗", "Tendencia"),
    "anomalies": ("⚡", "Anomalía"),
    "correlations": ("⟷", "Correlación"),
    "recommendations": ("→", "Recomendación"),
}


def _insights_table(insights: dict, styles: dict) -> list:
    items: list[tuple[str, str, str]] = []
    for category, entries in insights.items():
        icon, label = _CATEGORY_LABEL.get(category, ("•", category.title()))
        for entry in entries:
            items.append((f"{icon} {label}", entry.get("title", ""), entry.get("description", "")))
        if len(items) >= 8:
            break

    rows = []
    for tag, title, desc in items[:8]:
        rows.append([
            Paragraph(tag, styles["small"]),
            [Paragraph(title, styles["insight_title"]), Paragraph(desc, styles["insight_body"])],
        ])

    if not rows:
        return []

    t = Table(rows, colWidths=[3 * cm, 14 * cm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_SURFACE, _BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, _BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [t]


def generate_report(
    filename: str,
    profile: dict[str, Any],
    insights: dict[str, Any] | None,
    predictions: dict[str, Any] | None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("DataInsight AI", styles["title"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        f"Informe de análisis  ·  {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_hr())

    # ── Dataset summary ───────────────────────────────────────────────────────
    story.append(Paragraph("Resumen del dataset", styles["section"]))
    stats: list[tuple[str, str]] = [
        ("Archivo", filename),
        ("Filas", f"{profile.get('row_count', 0):,}"),
        ("Columnas", str(profile.get("column_count", 0))),
    ]
    if profile.get("date_column_candidate"):
        stats.append(("Columna fecha", profile["date_column_candidate"]))
    story.append(_stat_table(stats, styles))
    story.append(Spacer(1, 0.4 * cm))

    # ── Columns ───────────────────────────────────────────────────────────────
    columns = profile.get("columns", [])
    if columns:
        story.append(Paragraph("Perfilado de columnas", styles["section"]))
        story.append(_columns_table(columns, styles))
        story.append(Spacer(1, 0.4 * cm))

    # ── Insights ──────────────────────────────────────────────────────────────
    if insights:
        total = sum(len(v) for v in insights.values())
        if total > 0:
            story.append(_hr())
            story.append(Paragraph(f"Insights generados por IA  ({total})", styles["section"]))
            story.extend(_insights_table(insights, styles))
            story.append(Spacer(1, 0.4 * cm))

    # ── Predictions ───────────────────────────────────────────────────────────
    if predictions:
        forecast = predictions.get("forecast")
        regression = predictions.get("regression")

        if forecast and forecast.get("points"):
            story.append(_hr())
            story.append(Paragraph("Predicciones — serie temporal", styles["section"]))
            pred_stats: list[tuple[str, str]] = [
                ("Objetivo", forecast["target_column"]),
                ("Columna fecha", forecast["date_column"]),
                ("Horizonte", f"{forecast.get('horizon_days', 30)} días"),
            ]
            if forecast.get("mape") is not None:
                pred_stats.append(("MAPE backtest", f"{forecast['mape']:.1f}%"))
            story.append(_stat_table(pred_stats, styles))

            points = forecast["points"][:5]
            p_header = [Paragraph(h, styles["small"]) for h in ["Fecha", "Predicción", "IC inferior", "IC superior"]]
            p_rows = [p_header] + [
                [Paragraph(p["ds"], styles["body"]),
                 Paragraph(f"{p['yhat']:.2f}", styles["body"]),
                 Paragraph(f"{p['yhat_lower']:.2f}", styles["small"]),
                 Paragraph(f"{p['yhat_upper']:.2f}", styles["small"])]
                for p in points
            ]
            pt = Table(p_rows, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
            pt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_SURFACE, _BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(Spacer(1, 0.3 * cm))
            story.append(pt)
            story.append(Paragraph("Mostrando los primeros 5 puntos del forecast.", styles["small"]))
            story.append(Spacer(1, 0.4 * cm))

        if regression and regression.get("feature_importance"):
            story.append(_hr())
            story.append(Paragraph("Regresión baseline (RandomForest)", styles["section"]))
            reg_stats: list[tuple[str, str]] = [
                ("Objetivo", regression["target_column"]),
                ("R²", f"{regression['r2']:.3f}"),
                ("RMSE", f"{regression['rmse']:.2f}"),
            ]
            story.append(_stat_table(reg_stats, styles))

            fi = regression["feature_importance"][:10]
            fi_header = [Paragraph(h, styles["small"]) for h in ["Variable", "Importancia"]]
            fi_rows = [fi_header] + [
                [Paragraph(f["feature"], styles["body"]),
                 Paragraph(f"{f['importance'] * 100:.1f}%", styles["body"])]
                for f in fi
            ]
            fit = Table(fi_rows, colWidths=[10 * cm, 4 * cm])
            fit.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_SURFACE, _BG]),
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(Spacer(1, 0.3 * cm))
            story.append(fit)

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(_hr())
    story.append(Paragraph(
        "Generado automáticamente por DataInsight AI · Los insights han sido producidos por un modelo de lenguaje y deben verificarse.",
        styles["small"],
    ))

    def _on_page(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(_BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(_MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
