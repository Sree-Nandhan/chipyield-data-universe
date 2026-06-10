#!/usr/bin/env python3
"""Train a sklearn classifier on the gold mart_ml_features table."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import duckdb
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "chipyield.duckdb"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


def load_gold_mart(db_path: Path):
    con = duckdb.connect(str(db_path), read_only=True)
    row = con.execute(
        """
        SELECT table_schema
        FROM information_schema.tables
        WHERE table_name = 'mart_ml_features'
        LIMIT 1
        """
    ).fetchone()
    if not row:
        raise RuntimeError("mart_ml_features not found. Run dbt first.")

    schema = row[0]
    df = con.execute(f'SELECT * FROM "{schema}".mart_ml_features ORDER BY wafer_id').fetchdf()
    con.close()

    if df.empty:
        raise RuntimeError("mart_ml_features is empty. Run dbt first.")

    feature_cols = sorted(
        [c for c in df.columns if re.fullmatch(r"feature_\d{3}", c)],
        key=lambda c: int(c.split("_")[1]),
    )
    X = df[feature_cols].astype(float)
    y = df["is_fail"].astype(int)
    return df, X, y, feature_cols


def train(db_path: Path) -> dict:
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    df, X, y, feature_cols = load_gold_mart(db_path)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "rows_total": int(len(df)),
        "rows_train": int(len(X_train)),
        "rows_test": int(len(X_test)),
        "feature_count": len(feature_cols),
        "positive_rate_pct": round(100.0 * y.mean(), 2),
        "f1_fail_class": round(float(f1_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "precision_fail": round(float(precision_recall_fscore_support(y_test, y_pred)[0][1]), 4),
        "recall_fail": round(float(precision_recall_fscore_support(y_test, y_pred)[1][1]), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "top_features": sorted(
            zip(feature_cols, model.feature_importances_.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )[:10],
    }

    metrics_path = ARTIFACTS_DIR / "model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))

    import joblib

    joblib.dump(model, ARTIFACTS_DIR / "yield_classifier.joblib")

    print("Classifier trained on gold mart_ml_features")
    print(f"  Rows: {metrics['rows_total']} | Features: {metrics['feature_count']}")
    print(f"  ROC-AUC: {metrics['roc_auc']} | F1 (fail): {metrics['f1_fail_class']}")
    print(f"  Metrics saved -> {metrics_path}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train yield classifier from dbt gold mart")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    train(args.db)


if __name__ == "__main__":
    main()
