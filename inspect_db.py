import sqlite3

DB = "DB/nifty100.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 70)
print("DATABASE TABLE INSPECTION")
print("=" * 70)

tables = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print("\nTABLES:")
for table in tables:
    print(" -", table[0])

for (table_name,) in tables:
    print("\n" + "=" * 70)
    print(f"TABLE: {table_name}")
    print("=" * 70)

    columns = cur.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    print("COLUMNS:")
    for col in columns:
        print(col)

    count = cur.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print("ROWS:", count)

    print("SAMPLE:")
    rows = cur.execute(
        f"SELECT * FROM {table_name} LIMIT 3"
    ).fetchall()

    for row in rows:
        print(row)

conn.close()

print("\n" + "=" * 70)
print("INSPECTION COMPLETED")
print("=" * 70)