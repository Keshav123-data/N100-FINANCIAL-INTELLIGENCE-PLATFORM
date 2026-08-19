import sqlite3

p = "DB/nifty100.db"

c = sqlite3.connect(p)

print("Database:", p)
print("Integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])

print(
    "financial_ratios rows:",
    c.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
)

print("Tables:")

for row in c.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
):
    print(" -", row[0])

c.close()