CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    contact_name VARCHAR(200) DEFAULT '',
    phone VARCHAR(50) DEFAULT '',
    email VARCHAR(254) DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_suppliers_id ON suppliers(id);
CREATE INDEX IF NOT EXISTS ix_suppliers_name ON suppliers(name);
