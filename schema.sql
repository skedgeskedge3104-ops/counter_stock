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
    pos_code INTEGER,
    maker VARCHAR(32),
    category_name VARCHAR(16),
    shop_name VARCHAR(16)
        REFERENCES shops(shop_name),
    group_name VARCHAR(16) NOT NULL
        REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) PRIMARY KEY,
    quantity_box INTEGER,
    unit_price NUMERIC(5,2),
    expiry_date TIMESTAMP,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE
);

CREATE TABLE IF NOT EXISTS product_price_periods (
    price_period_id SERIAL PRIMARY KEY,
    product_name VARCHAR(64) NOT NULL
        REFERENCES products(product_name),
    price_group_name VARCHAR(16) NOT NULL
        REFERENCES group_by_counts(group_name),
    unit_price NUMERIC(5,2) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (effective_to IS NULL OR effective_from < effective_to)
);

CREATE INDEX IF NOT EXISTS idx_price_periods_product_from
    ON product_price_periods(product_name, effective_from DESC);




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

-- 既存DB向け: inventory_in.price_period_id がなければ追加
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'inventory_in'
    )
    AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'inventory_in'
          AND column_name = 'price_period_id'
    ) THEN
        ALTER TABLE inventory_in ADD COLUMN price_period_id INTEGER;
    END IF;
END$$;

-- 既存DB向け: inventory_out.price_period_id がなければ追加
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'inventory_out'
    )
    AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'inventory_out'
          AND column_name = 'price_period_id'
    ) THEN
        ALTER TABLE inventory_out ADD COLUMN price_period_id INTEGER;
    END IF;
END$$;

-- 既存DB向け: 価格期間FK（inventory_in）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'inventory_in'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'inventory_in_price_period_id_fkey'
    ) THEN
        ALTER TABLE inventory_in
        ADD CONSTRAINT inventory_in_price_period_id_fkey
        FOREIGN KEY (price_period_id)
        REFERENCES product_price_periods(price_period_id);
    END IF;
END$$;

-- 既存DB向け: 価格期間FK（inventory_out）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'inventory_out'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'inventory_out_price_period_id_fkey'
    ) THEN
        ALTER TABLE inventory_out
        ADD CONSTRAINT inventory_out_price_period_id_fkey
        FOREIGN KEY (price_period_id)
        REFERENCES product_price_periods(price_period_id);
    END IF;
END$$;

-- 既存DB向け: products.pos_code がなければ追加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name = 'pos_code'
    ) THEN
        ALTER TABLE products ADD COLUMN pos_code INTEGER;
    END IF;
END$$;

-- 既存DB向け: products.effective_from がなければ追加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name = 'effective_from'
    ) THEN
        ALTER TABLE products ADD COLUMN effective_from DATE;
    END IF;
END$$;

-- 既存DB向け: products.effective_to がなければ追加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name = 'effective_to'
    ) THEN
        ALTER TABLE products ADD COLUMN effective_to DATE;
    END IF;
END$$;

-- 既存DB向け: effective_from のNULLを埋めて NOT NULL / DEFAULT を付与
UPDATE products
SET effective_from = CURRENT_DATE
WHERE effective_from IS NULL;

ALTER TABLE products
ALTER COLUMN effective_from SET DEFAULT CURRENT_DATE;

ALTER TABLE products
ALTER COLUMN effective_from SET NOT NULL;

-- 既存DB向け: products.display があれば削除（有効期間管理へ移行）
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name = 'display'
    ) THEN
        ALTER TABLE products DROP COLUMN display;
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
    price_period_id INTEGER,
    received_quantity INTEGER NOT NULL,
    received_day TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_name, group_name)
        REFERENCES products(product_name, group_name),
    FOREIGN KEY (price_period_id)
        REFERENCES product_price_periods(price_period_id)
);


CREATE TABLE IF NOT EXISTS inventory_out (
    out_id SERIAL PRIMARY KEY,
    product_name VARCHAR(64) NOT NULL,
    group_name VARCHAR(16) NOT NULL,
    price_period_id INTEGER,
    shipped_quantity INTEGER NOT NULL,
    shipped_day TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_name, group_name)
        REFERENCES products(product_name, group_name),
    FOREIGN KEY (price_period_id)
        REFERENCES product_price_periods(price_period_id)
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

CREATE TABLE IF NOT EXISTS inventory_check_drafts (
    draft_key VARCHAR(64) PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_check_results (
    result_id SERIAL PRIMARY KEY,
    category_name VARCHAR(16) NOT NULL
        REFERENCES categories(category_name),
    pos_code INTEGER,
    group_name VARCHAR(16) NOT NULL
        REFERENCES group_by_counts(group_name),
    product_name VARCHAR(64) NOT NULL,
    db_stock_count INTEGER NOT NULL,
    counted_stock_count INTEGER NOT NULL,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
