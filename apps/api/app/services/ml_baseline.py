from __future__ import annotations

import io
import math
from typing import Any

import numpy as np
import pandas as pd


def run_regression(content: bytes, target_col: str, feature_cols: list[str]) -> dict[str, Any]:
    from sklearn.ensemble import RandomForestRegressor  # type: ignore[import-untyped]
    from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
    from sklearn.metrics import r2_score, root_mean_squared_error  # type: ignore[import-untyped]
    from sklearn.preprocessing import LabelEncoder  # type: ignore[import-untyped]

    df = pd.read_csv(io.BytesIO(content))
    cols = [c for c in [target_col] + feature_cols if c in df.columns]
    df = df[cols].dropna()

    if len(df) < 20:
        return {"target_column": target_col, "r2": 0.0, "rmse": 0.0, "feature_importance": []}

    X = df[feature_cols].copy()
    y = df[target_col].astype(float)

    # Encode categoricals
    for col in X.select_dtypes(include="object").columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))

    X = X.astype(float)

    test_size = max(0.1, min(0.3, 50 / len(df)))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    n_estimators = 100 if len(X_train) > 1000 else 50
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = float(r2_score(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))

    importance = sorted(
        zip(feature_cols, model.feature_importances_.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "target_column": target_col,
        "r2": r2,
        "rmse": rmse,
        "feature_importance": [{"feature": f, "importance": round(imp, 4)} for f, imp in importance[:15]],
    }
