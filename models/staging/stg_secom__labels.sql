with source as (
    select * from {{ source('bronze', 'secom_labels_raw') }}
),

parsed as (
    select
        wafer_id,
        pass_fail_raw,
        case
            when pass_fail_raw = 1 then 'pass'
            when pass_fail_raw = -1 then 'fail'
            else 'unknown'
        end as yield_status,
        case
            when pass_fail_raw = 1 then 0
            when pass_fail_raw = -1 then 1
            else null
        end as is_fail,
        try_strptime(timestamp_str, '%d/%m/%Y %H:%M:%S') as tested_at
    from source
)

select * from parsed
