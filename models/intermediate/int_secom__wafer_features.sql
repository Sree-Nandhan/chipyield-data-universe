with imputed as (
    select
        i.wafer_id,
        i.sensor_id,
        i.reading_value,
        i.was_imputed,
        q.sensor_rank
    from {{ ref('int_secom__imputed_readings') }} as i
    inner join {{ ref('int_secom__sensor_quality') }} as q using (sensor_id)
    where q.is_selected_for_ml
),

pivoted as (
    select
        wafer_id,
        max(case when was_imputed then 1 else 0 end) as any_imputed_flag,
        sum(case when was_imputed then 1 else 0 end) as imputed_sensor_count,
        {% for rank in range(1, 51) %}
        max(case when sensor_rank = {{ rank }} then reading_value end) as feature_{{ '%03d' | format(rank) }}{% if not loop.last %},{% endif %}
        {% endfor %}
    from imputed
    group by 1
)

select * from pivoted
