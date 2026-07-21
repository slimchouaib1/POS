import os

import psycopg2
from psycopg2 import sql

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is required")
database_url = database_url.replace("postgresql+psycopg2://", "postgresql://", 1)

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Fix all sequences so auto-increment continues from the right value
cursor.execute("""
    SELECT table_name, column_name 
    FROM information_schema.columns 
    WHERE column_default LIKE 'nextval%' AND table_schema = 'public'
""")

for table_name, column_name in cursor.fetchall():
    cursor.execute(
        sql.SQL("SELECT MAX({column}) FROM {table}").format(
            column=sql.Identifier(column_name),
            table=sql.Identifier(table_name),
        )
    )
    max_val = cursor.fetchone()[0]
    if max_val is not None:
        cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", (table_name, column_name))
        seq_name = cursor.fetchone()[0]
        cursor.execute("SELECT setval(%s, %s)", (seq_name, max_val))
        print(f"  Set {seq_name} to {max_val}")

conn.commit()
conn.close()
print("All sequences fixed!")
