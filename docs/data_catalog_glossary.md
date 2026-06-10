# ChipYield Data Catalog Glossary

## Lakehouse Layers

ChipYield uses a medallion-style layout on DuckDB:

- **Bronze**: Raw SECOM sensor readings and labels ingested without transformation (`bronze.secom_*` tables).
- **Silver (staging/intermediate)**: Cleaned, nullified, imputed, and feature-engineered datasets in dbt views.
- **Gold (marts)**: Analytics-ready and AI-ready curated tables for BI dashboards and ML training.

## Grain Definitions

- `stg_secom__readings`: one row per wafer_id + sensor_id pair.
- `stg_secom__labels`: one row per wafer_id (unique wafer test event).
- `int_secom__wafer_features`: one row per wafer_id with 50 engineered features.
- `mart_ml_features`: one row per wafer_id — **primary ML training dataset**.
- `mart_yield_analytics`: one row per test_date for daily yield KPI reporting.

## Key Business Terms

- **Yield**: Percentage of wafers passing electrical test (pass / total).
- **Fail rate**: Percentage of wafers failing test — inverse of yield for binary outcomes.
- **Wafer**: Manufacturing unit under test; identified by `wafer_id` in this demo dataset.
- **Sensor channel**: Individual sensor measurement column (591 in source SECOM data).

## AI-Ready Data Rules

- ML models must consume `mart_ml_features` only — never raw bronze tables.
- Target column for failure prediction is `is_fail` (1 = fail, 0 = pass).
- Features `feature_001` through `feature_050` are top variance-ranked sensors with median imputation.
- `feature_set_built_at` tracks when the gold feature mart was last materialized by dbt.

## Data Quality Expectations

- `wafer_id` must be unique in label and ML marts.
- `yield_status` accepts only `pass` or `fail`.
- Sentinel value `-200` in source readings is converted to null in staging.
- Sensors with high null rates are excluded from ML feature selection.

## Production context

This project uses the public UCI SECOM dataset as a semiconductor manufacturing proxy. The same patterns apply to production lakehouse platforms: raw ingest, tested SQL transforms, curated gold marts, and catalog discovery for analytics and ML teams.
