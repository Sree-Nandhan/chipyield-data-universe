{% macro nullify_sentinel(column_name, sentinel=var('secom_sentinel')) %}
    case
        when {{ column_name }} = {{ sentinel }} then null
        else {{ column_name }}
    end
{% endmacro %}
