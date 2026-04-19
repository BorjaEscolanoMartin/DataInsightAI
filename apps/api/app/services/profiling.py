import io
import math
from typing import Any
import pandas as pd
import numpy as np


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _infer_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_string_dtype(series) or series.dtype == object:
        non_null = series.dropna()
        if len(non_null) > 0:
            sample = str(non_null.iloc[0])
            if any(c in sample for c in ["-", "/", ":"]):
                try:
                    pd.to_datetime(non_null.head(50), format="mixed", dayfirst=False)
                    return "date"
                except Exception:
                    pass
        n = len(series)
        if n > 0 and series.nunique() <= min(50, n * 0.5):
            return "categorical"
        return "text"
    return "categorical"


def _outliers_iqr(series: pd.Series) -> int:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    return int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())


def _compute_charts(df: pd.DataFrame, columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    col_types = {c["name"]: c["type"] for c in columns}

    numeric_cols = [c for c, t in col_types.items() if t == "numeric" and c in df.columns]
    cat_cols = [c for c, t in col_types.items() if t == "categorical" and c in df.columns]
    date_candidate = next((c for c, t in col_types.items() if t == "date" and c in df.columns), None)

    # Histograms — max 6 numeric columns
    for col in numeric_cols[:6]:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 2:
            continue
        counts, edges = np.histogram(series, bins=20)
        charts.append({
            "id": f"hist_{col}",
            "type": "histogram",
            "title": f"Distribución de {col}",
            "column": col,
            "data": [
                {"bin": f"{edges[i]:.4g}–{edges[i+1]:.4g}", "count": int(counts[i])}
                for i in range(len(counts))
                if counts[i] > 0
            ],
        })

    # Bar charts — max 4 categorical columns
    for col in cat_cols[:4]:
        col_data = next((c for c in columns if c["name"] == col), None)
        if not col_data or not col_data.get("top_categories"):
            continue
        charts.append({
            "id": f"bar_{col}",
            "type": "bar",
            "title": f"Top valores de {col}",
            "column": col,
            "data": [
                {"name": c["value"], "count": c["count"]}
                for c in col_data["top_categories"]
            ],
        })

    # Correlation heatmap — need >= 3 numeric cols
    corr_matrix: pd.DataFrame | None = None
    if len(numeric_cols) >= 3:
        try:
            heat_cols = numeric_cols[:15]
            corr_matrix = df[heat_cols].apply(pd.to_numeric, errors="coerce").corr()
            heatmap_data = [
                {"x": col_a, "y": col_b, "value": round(float(corr_matrix.loc[col_a, col_b]), 3)}
                for col_a in heat_cols
                for col_b in heat_cols
                if not math.isnan(corr_matrix.loc[col_a, col_b])
            ]
            if heatmap_data:
                charts.append({
                    "id": "correlation_heatmap",
                    "type": "heatmap",
                    "title": "Correlación entre variables numéricas",
                    "columns": heat_cols,
                    "data": heatmap_data,
                })
        except Exception:
            pass

    # Time series line chart
    if date_candidate and numeric_cols:
        try:
            y_col = numeric_cols[0]
            df_ts = df[[date_candidate, y_col]].copy()
            df_ts[date_candidate] = pd.to_datetime(df_ts[date_candidate], format="mixed", dayfirst=False, errors="coerce")
            df_ts = df_ts.dropna().sort_values(date_candidate)
            if len(df_ts) > 500:
                step = max(1, len(df_ts) // 500)
                df_ts = df_ts.iloc[::step]
            line_data = [
                {"date": row[date_candidate].isoformat(), "value": _safe_float(row[y_col])}
                for _, row in df_ts.iterrows()
                if _safe_float(row[y_col]) is not None
            ]
            if line_data:
                charts.append({
                    "id": f"line_{y_col}",
                    "type": "line",
                    "title": f"Evolución de {y_col}",
                    "x_column": date_candidate,
                    "y_column": y_col,
                    "data": line_data,
                })
        except Exception:
            pass

    # Scatter — top 2 pairs with |r| > 0.5
    if len(numeric_cols) >= 2:
        try:
            sc_cols = numeric_cols[:10]
            if corr_matrix is None:
                corr_matrix = df[sc_cols].apply(pd.to_numeric, errors="coerce").corr()
            pairs: list[tuple[float, str, str]] = []
            for i, col_a in enumerate(sc_cols):
                for col_b in sc_cols[i + 1 :]:
                    r = corr_matrix.loc[col_a, col_b]
                    if not math.isnan(r) and abs(r) > 0.5 and col_a != col_b:
                        pairs.append((abs(r), col_a, col_b))
            pairs.sort(reverse=True)
            for _, col_a, col_b in pairs[:2]:
                sc_df = df[[col_a, col_b]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(sc_df) > 300:
                    sc_df = sc_df.sample(300, random_state=42)
                charts.append({
                    "id": f"scatter_{col_a}_{col_b}",
                    "type": "scatter",
                    "title": f"{col_a} vs {col_b}",
                    "x_column": col_a,
                    "y_column": col_b,
                    "data": [
                        {"x": _safe_float(row[col_a]), "y": _safe_float(row[col_b])}
                        for _, row in sc_df.iterrows()
                    ],
                })
        except Exception:
            pass

    return charts


def profile_csv(content: bytes) -> dict[str, Any]:
    df: pd.DataFrame | None = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(content), sep=None, engine="python", encoding=encoding)
            break
        except Exception:
            continue
    if df is None:
        raise ValueError("No se pudo leer el CSV con las codificaciones soportadas")

    columns: list[dict[str, Any]] = []
    date_candidate: str | None = None

    for col in df.columns:
        series = df[col]
        col_type = _infer_type(series)
        total = len(series)
        null_count = int(series.isna().sum())

        entry: dict[str, Any] = {
            "name": col,
            "type": col_type,
            "null_count": null_count,
            "null_pct": round(null_count / total * 100, 2) if total > 0 else 0.0,
            "unique_count": int(series.nunique()),
        }

        if col_type == "numeric":
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            entry.update({
                "mean": _safe_float(numeric.mean()),
                "std": _safe_float(numeric.std()),
                "min_val": _safe_float(numeric.min()),
                "max_val": _safe_float(numeric.max()),
                "p25": _safe_float(numeric.quantile(0.25)),
                "p50": _safe_float(numeric.quantile(0.50)),
                "p75": _safe_float(numeric.quantile(0.75)),
                "outlier_count": _outliers_iqr(numeric),
            })
        elif col_type in ("categorical", "boolean"):
            top = series.value_counts().head(10)
            entry["top_categories"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]
        elif col_type == "date" and date_candidate is None:
            date_candidate = col

        columns.append(entry)

    charts = _compute_charts(df, columns)

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns,
        "date_column_candidate": date_candidate,
        "charts": charts,
    }
