sql_create_product_table = """
CREATE TABLE {}(
    product_id_db serial PRIMARY KEY,
    product_id text,
    product_name text,
    brand_id int,
    brand_name text,
    loves_count int,
    rating numeric,
    reviews int,
    size text,
    variation_type text,
    variation_value text,
    variation_desc text,
    ingredients text[],
    price_usd numeric,
    value_price_usd numeric,
    sale_price_usd numeric,
    limited_edition int,
    new int,
    online_only int,
    out_of_stock int,
    sephora_exclusive int,
    highlights text[],
    primary_category text,
    secondary_category text,
    tertiary_category text,
    child_count int,
    child_max_price numeric,
    child_min_price numeric);
"""

sql_create_brand_table = """
CREATE TABLE {}(
    brand_id_db serial PRIMARY KEY,
    brand_id int,
    brand_name text,
    products text[],
    total_products int);
"""