import os
import sqlite3
import psycopg2
import pandas as pd
from app.core.database import init_db

print("Initializing PostgreSQL schema...")
# This creates the tables using SQLAlchemy models
init_db()
print("Schema created.")

sqlite_path = "pos.db"
pg_url = os.environ.get("DATABASE_URL")
if not pg_url:
    raise RuntimeError("DATABASE_URL is required")
psycopg_url = pg_url.replace("postgresql+psycopg2://", "postgresql://", 1)


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'

print("Connecting to SQLite...")
sqlite_conn = sqlite3.connect(sqlite_path)
cursor = sqlite_conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

print(f"Found tables in SQLite: {tables}")

print("Connecting to PostgreSQL...")
pg_conn = psycopg2.connect(psycopg_url)
pg_cursor = pg_conn.cursor()

# Disable foreign key checks for this session
pg_cursor.execute("SET session_replication_role = 'replica';")
pg_conn.commit()

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.sql.sqltypes import Boolean
pg_engine = create_engine(pg_url)

metadata = MetaData()
metadata.reflect(bind=pg_engine)

# Truncate all tables to avoid duplicate key errors from any auto-seeding
with pg_engine.begin() as conn:
    for table in reversed(metadata.sorted_tables):
        conn.execute(text(f"TRUNCATE TABLE {quote_identifier(table.name)} CASCADE;"))

for table in tables:
    print(f"Migrating table {table}...")
    df = pd.read_sql_query(f"SELECT * FROM {quote_identifier(table)}", sqlite_conn)
    if not df.empty:
        pg_table = metadata.tables.get(table)
        if pg_table is not None:
            for col in pg_table.columns:
                if isinstance(col.type, Boolean) and col.name in df.columns:
                    # Convert 1/0 to True/False
                    df[col.name] = df[col.name].fillna(0).astype(bool)
                    
        # Write to PostgreSQL
        df.to_sql(table, pg_engine, if_exists='append', index=False)
        print(f"  Migrated {len(df)} rows.")
    else:
        print("  Table is empty.")

# Re-enable foreign key checks
from sqlalchemy import text
with pg_engine.connect() as conn:
    conn.execute(text("SET session_replication_role = 'origin';"))
    conn.commit()

print("Migration completed successfully!")
sqlite_conn.close()
pg_conn.close()
