import psycopg2

for port in [5432, 5433]:
    try:
        conn = psycopg2.connect(f"postgresql://pos_dev:pos_dev_password@localhost:{port}/pos_dev")
        cur = conn.cursor()
        cur.execute("ALTER TABLE tables ADD COLUMN IF NOT EXISTS current_covers INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE tables ADD COLUMN IF NOT EXISTS reservation_time VARCHAR(50) DEFAULT '';")
        cur.execute("UPDATE tables SET current_covers = 2, reservation_time = '19:30' WHERE number = 2;")
        cur.execute("UPDATE tables SET current_covers = 3, reservation_time = '20:00' WHERE number = 7;")
        conn.commit()
        conn.close()
        print(f"Port {port} updated successfully")
    except Exception as e:
        print(f"Port {port} note: {e}")
