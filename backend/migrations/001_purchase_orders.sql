CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    quantity_ordered DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP NULL,
    created_by INTEGER NULL REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_purchase_orders_id ON purchase_orders(id);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_ingredient_id ON purchase_orders(ingredient_id);
CREATE INDEX IF NOT EXISTS ix_purchase_orders_status ON purchase_orders(status);
