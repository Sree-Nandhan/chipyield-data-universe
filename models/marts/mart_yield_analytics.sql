with labels as (
    select * from {{ ref('stg_secom__labels') }}
),

daily as (
    select
        cast(tested_at as date) as test_date,
        count(*) as wafer_count,
        sum(is_fail) as fail_count,
        count(*) - sum(is_fail) as pass_count,
        round(100.0 * sum(is_fail) / count(*), 2) as fail_rate_pct,
        round(100.0 * (count(*) - sum(is_fail)) / count(*), 2) as yield_rate_pct
    from labels
    where tested_at is not null
    group by 1
)

select * from daily
order by test_date
