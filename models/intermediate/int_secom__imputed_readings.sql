with readings as (
    select * from {{ ref('stg_secom__readings') }}
),

selected_sensors as (
    select sensor_id
    from {{ ref('int_secom__sensor_quality') }}
    where is_selected_for_ml
),

filtered as (
    select r.*
    from readings as r
    inner join selected_sensors as s using (sensor_id)
),

sensor_medians as (
    select
        sensor_id,
        median(reading_value) as sensor_median
    from filtered
    group by 1
),

imputed as (
    select
        f.wafer_id,
        f.sensor_id,
        coalesce(f.reading_value, m.sensor_median) as reading_value,
        f.reading_value is null as was_imputed
    from filtered as f
    left join sensor_medians as m using (sensor_id)
)

select * from imputed
