CREATE TABLE IF NOT EXISTS categries(
    category_id SERIAL PRIMARY KEY,
    category_name UNIQUE VARCHAR(16)
) ;

CREATE TABLE IF NOT EXISTS group_by_counts(
    group_no SERIAL,
    group_name PRIMARY KEY VARCHAR(16),
    values NUMERIC(5.1)
);

CREATE TABLE IF NOT EXISTS shops(
    shop_id SERIAL PRIMARY KEY,
    shop_name UNIQUE VARCHA(16)
);

CREATE TABLE IF NOT EXISTS products(
    product_no SERIAL,
    product_id UNIQUE VARCHAR(32),
    maker VARCHAR(32),
    category_name UNIQUE VARCHAR(16) REFERENCES categories(cateogry_name),
    shop_name UNIQUE VARCHAR(16) REFERENCES shops(shop_name),
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    product_name PRIMARY KEY VARCHAR(64) ,
    provisional_name VARCHAR(64),
    quantity_box INTEGER,
    unit_price NUMERIC(5.1),
    expiry_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_in(
    in_id SERIAL,
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) REFERENCES products(product_name),
    received_quani INTEGER,
    received_day TIMESTAMP
);


CREATE TABLE IF NOT EXISTS invenotry_out(
    out_id SERIAL,
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    shipped_quantity INTEGER,
    shipped_day TIMESTAMP
);