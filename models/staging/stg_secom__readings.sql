with source as (
    select * from {{ source('bronze', 'secom_sensor_readings_long') }}
),

cleaned as (
    select
        wafer_id,
        sensor_id,
        {{ nullify_sentinel('reading_value') }} as reading_value,
        case
            when reading_value = {{ var('secom_sentinel') }} then true
            else false
        end as is_imputed_source_missing
    from source
)

select * from cleaned
