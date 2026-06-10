with labels as (
    select * from {{ ref('stg_secom__labels') }}
),

summary as (
    select
        count(*) as total_wafers,
        sum(is_fail) as total_fails,
        count(*) - sum(is_fail) as total_passes,
        round(100.0 * sum(is_fail) / count(*), 2) as overall_fail_rate_pct,
        round(100.0 * (count(*) - sum(is_fail)) / count(*), 2) as overall_yield_rate_pct,
        min(tested_at) as first_test_at,
        max(tested_at) as last_test_at
    from labels
)

select * from summary
