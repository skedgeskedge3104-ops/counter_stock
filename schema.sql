CREATE TABLE IF NOT EXISTS categories(
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(16) UNIQUE
) ;

CREATE TABLE IF NOT EXISTS group_by_counts(
    group_no SERIAL,
    group_name VARCHAR(16) PRIMARY KEY,
    values NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS shops(
    shop_id SERIAL PRIMARY KEY,
    shop_name VARCHAR(16) UNIQUE
);

CREATE TABLE IF NOT EXISTS products(
    product_no SERIAL,
    product_id VARCHAR(32) UNIQUE,
    maker VARCHAR(32),
    category_name VARCHAR(16) UNIQUE REFERENCES categories(category_name),
    shop_name VARCHAR(16) UNIQUE REFERENCES shops(shop_name),
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) PRIMARY KEY ,
    provisional_name VARCHAR(64),
    quantity_box INTEGER,
    unit_price NUMERIC(5,2),
    expiry_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_in(
    in_id SERIAL,
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) REFERENCES products(product_name),
    received_quani INTEGER,
    received_day TIMESTAMP
);


CREATE TABLE IF NOT EXISTS inventory_out(
    out_id SERIAL,
    group_name VARCHAR(16) REFERENCES group_by_counts(group_name),
    shipped_quantity INTEGER,
    shipped_day TIMESTAMP
);