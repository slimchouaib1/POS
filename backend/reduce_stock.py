import os

import psycopg2

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is required")
database_url = database_url.replace("postgresql+psycopg2://", "postgresql://", 1)

conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Reduce stock for all products to a small number between 5 and 15 so that shortages trigger
# Wait, let's just reduce all of them to 5.
cursor.execute("UPDATE products SET stock_quantity = 5")

conn.commit()
conn.close()
print("Stock reduced for all products.")
