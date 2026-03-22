 CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(16) UNIQUE NOT NULL
);

CREATE TABLE  IF NOT EXISTS group_by_counts (
    group_no SERIAL,
    group_name VARCHAR(16) PRIMARY KEY,
    values NUMERIC(5,2)
   );

ALTER TABLE group_by_counts ALTER COLUMN values TYPE NUMERIC(6,2);

CREATE TABLE  IF NOT EXISTS shops (
    shop_id SERIAL PRIMARY KEY,
    shop_name VARCHAR(16) UNIQUE NOT NULL
);


CREATE TABLE IF NOT EXISTS products (
    product_no SERIAL,
    product_id VARCHAR(32),
    maker VARCHAR(32),
    shop_name VARCHAR(16)
        REFERENCES shops(shop_name),
    group_name VARCHAR(16) NOT NULL
        REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) PRIMARY KEY,
    quantity_box INTEGER,
    unit_price NUMERIC(5,2),
    expiry_date TIMESTAMP
);




DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'products_product_group_unique'
    ) THEN
        ALTER TABLE products
        ADD CONSTRAINT products_product_group_unique
        UNIQUE (product_name, group_name);
    END IF;
END$$;

-- アプリが参照するカテゴリ（既存DBで欠けていると SQL が失敗する）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name = 'category_name'
    ) THEN
        ALTER TABLE products ADD COLUMN category_name VARCHAR(16);
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS inventory_in (
    in_id SERIAL PRIMARY KEY,
    product_name VARCHAR(64) NOT NULL,
    group_name VARCHAR(16) NOT NULL,
    received_quantity INTEGER NOT NULL,
    received_day TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_name, group_name)
        REFERENCES products(product_name, group_name)
);


CREATE TABLE IF NOT EXISTS inventory_out (
    out_id SERIAL PRIMARY KEY,
    product_name VARCHAR(64) NOT NULL,
    group_name VARCHAR(16) NOT NULL,
    shipped_quantity INTEGER NOT NULL,
    shipped_day TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_name, group_name)
        REFERENCES products(product_name, group_name)
);

CREATE TABLE IF NOT EXISTS inventory_check (
    check_id SERIAL PRIMARY KEY,
    category_name VARCHAR(16) NOT NULL
        REFERENCES categories(category_name),
    product_name VARCHAR(64) NOT NULL
        REFERENCES products(product_name),
    group_name VARCHAR(16) NOT NULL
        REFERENCES group_by_counts(group_name),

    check_date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    in_shelf_count INTEGER NOT NULL,
    unit_count INTEGER NOT NULL,
    pos_stock INTEGER NOT NULL,

    checked_by VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (product_name, group_name, check_date)
);
