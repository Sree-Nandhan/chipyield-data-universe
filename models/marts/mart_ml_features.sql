with features as (
    select * from {{ ref('int_secom__wafer_features') }}
),

labels as (
    select
        wafer_id,
        yield_status,
        is_fail,
        tested_at
    from {{ ref('stg_secom__labels') }}
),

final as (
    select
        f.wafer_id,
        l.yield_status,
        l.is_fail,
        l.tested_at,
        cast(l.tested_at as date) as test_date,
        f.any_imputed_flag,
        f.imputed_sensor_count,
        f.feature_001,
        f.feature_002,
        f.feature_003,
        f.feature_004,
        f.feature_005,
        f.feature_006,
        f.feature_007,
        f.feature_008,
        f.feature_009,
        f.feature_010,
        f.feature_011,
        f.feature_012,
        f.feature_013,
        f.feature_014,
        f.feature_015,
        f.feature_016,
        f.feature_017,
        f.feature_018,
        f.feature_019,
        f.feature_020,
        f.feature_021,
        f.feature_022,
        f.feature_023,
        f.feature_024,
        f.feature_025,
        f.feature_026,
        f.feature_027,
        f.feature_028,
        f.feature_029,
        f.feature_030,
        f.feature_031,
        f.feature_032,
        f.feature_033,
        f.feature_034,
        f.feature_035,
        f.feature_036,
        f.feature_037,
        f.feature_038,
        f.feature_039,
        f.feature_040,
        f.feature_041,
        f.feature_042,
        f.feature_043,
        f.feature_044,
        f.feature_045,
        f.feature_046,
        f.feature_047,
        f.feature_048,
        f.feature_049,
        f.feature_050,
        current_timestamp as feature_set_built_at
    from features as f
    inner join labels as l using (wafer_id)
)

select * from final
