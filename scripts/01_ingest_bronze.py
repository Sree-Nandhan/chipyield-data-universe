#!/usr/bin/env python3
"""Bronze layer ingestion: raw SECOM files -> DuckDB bronze schema."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

SENTINEL = -200.0
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
DEFAULT_DB = PROJECT_ROOT / "chipyield.duckdb"


def load_raw_features(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None, engine="python")
    df.columns = [f"sensor_{i + 1:03d}" for i in range(df.shape[1])]
    df.insert(0, "wafer_id", pd.Series(range(1, len(df) + 1), dtype="int64"))
    return df.copy()


def load_raw_labels(path: Path) -> pd.DataFrame:
    rows = []
    for line in path.read_text().strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: -1 "19/07/2008 11:55:00"
        if '"' in line:
            label_part, ts_part = line.split('"', 1)
            label = int(label_part.strip())
            timestamp = ts_part.replace('"', "").strip()
        else:
            parts = line.split()
            label = int(parts[0])
            timestamp = parts[1] if len(parts) > 1 else None
        rows.append({"pass_fail_raw": label, "timestamp_str": timestamp})

    df = pd.DataFrame(rows)
    df.insert(0, "wafer_id", range(1, len(df) + 1))
    return df


def to_long_format(wide: pd.DataFrame) -> pd.DataFrame:
    long_df = wide.melt(id_vars=["wafer_id"], var_name="sensor_id", value_name="reading_value")
    long_df["sensor_id"] = long_df["sensor_id"].str.replace("sensor_", "", regex=False).astype(int)
    return long_df


def ingest(db_path: Path) -> None:
    features_path = BRONZE_DIR / "secom.data"
    labels_path = BRONZE_DIR / "secom_labels.data"

    if not features_path.exists() or not labels_path.exists():
        raise FileNotFoundError(
            f"Missing SECOM files in {BRONZE_DIR}. "
            "Download secom.data and secom_labels.data from UCI first."
        )

    wide = load_raw_features(features_path)
    labels = load_raw_labels(labels_path)
    long_readings = to_long_format(wide)

    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    con.register("wide_df", wide)
    con.register("labels_df", labels)
    con.register("long_df", long_readings)

    con.execute("DROP TABLE IF EXISTS bronze.secom_sensor_readings_wide")
    con.execute("DROP TABLE IF EXISTS bronze.secom_sensor_readings_long")
    con.execute("DROP TABLE IF EXISTS bronze.secom_labels_raw")

    con.execute(
        """
        CREATE TABLE bronze.secom_sensor_readings_wide AS
        SELECT * FROM wide_df
        """
    )
    con.execute(
        """
        CREATE TABLE bronze.secom_sensor_readings_long AS
        SELECT * FROM long_df
        """
    )
    con.execute(
        """
        CREATE TABLE bronze.secom_labels_raw AS
        SELECT * FROM labels_df
        """
    )

    stats = con.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM bronze.secom_sensor_readings_wide) AS wafer_count,
            (SELECT COUNT(*) FROM bronze.secom_sensor_readings_long) AS reading_count,
            (SELECT COUNT(DISTINCT sensor_id) FROM bronze.secom_sensor_readings_long) AS sensor_count
        """
    ).fetchone()

    con.close()
    print(f"Bronze ingestion complete -> {db_path}")
    print(f"  Wafers: {stats[0]}, Readings: {stats[1]}, Sensors: {stats[2]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SECOM raw data into DuckDB bronze layer")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="DuckDB database path")
    args = parser.parse_args()
    ingest(args.db)


if __name__ == "__main__":
    main()
