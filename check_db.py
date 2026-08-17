import sqlite3

db_path = "DB/nifty100.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("DATABASE TABLES")
print("=" * 70)

tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
).fetchall()

for table in tables:
    print(table[0])


print("\n" + "=" * 70)
print("FINANCIAL RATIOS COLUMNS")
print("=" * 70)

try:
    columns = cursor.execute(
        "PRAGMA table_info(financial_ratios)"
    ).fetchall()

    for column in columns:
        print(column)

except Exception as e:
    print("ERROR:", e)


print("\n" + "=" * 70)
print("FINANCIAL RATIOS SAMPLE")
print("=" * 70)

try:
    rows = cursor.execute(
        "SELECT * FROM financial_ratios LIMIT 3"
    ).fetchall()

    for row in rows:
        print(row)

except Exception as e:
    print("ERROR:", e)


print("\n" + "=" * 70)
print("COMPANIES COLUMNS")
print("=" * 70)

try:
    columns = cursor.execute(
        "PRAGMA table_info(companies)"
    ).fetchall()

    for column in columns:
        print(column)

except Exception as e:
    print("ERROR:", e)


print("\n" + "=" * 70)
print("SECTORS COLUMNS")
print("=" * 70)

try:
    columns = cursor.execute(
        "PRAGMA table_info(sectors)"
    ).fetchall()

    for column in columns:
        print(column)

except Exception as e:
    print("ERROR:", e)


conn.close()

print("\nDatabase inspection completed.")