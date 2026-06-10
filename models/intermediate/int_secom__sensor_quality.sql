with readings as (
    select * from {{ ref('stg_secom__readings') }}
),

sensor_quality as (
    select
        sensor_id,
        count(*) as total_readings,
        count(reading_value) as non_null_readings,
        count(*) - count(reading_value) as null_readings,
        round(100.0 * (count(*) - count(reading_value)) / count(*), 2) as null_pct,
        stddev_samp(reading_value) as reading_stddev,
        avg(reading_value) as reading_mean
    from readings
    group by 1
),

ranked as (
    select
        *,
        row_number() over (
            order by
                case when null_pct <= {{ var('max_sensor_null_pct') }} * 100 then 0 else 1 end,
                reading_stddev desc nulls last
        ) as sensor_rank
    from sensor_quality
)

select
    sensor_id,
    total_readings,
    non_null_readings,
    null_readings,
    null_pct,
    reading_stddev,
    reading_mean,
    sensor_rank,
    sensor_rank <= {{ var('top_sensor_count') }} as is_selected_for_ml
from ranked
