from pathlib import Path
import sqlite3
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DB = ROOT / "DB" / "nifty100.db"

CHECKS = [
    ("D-01", "Sprint 1", "nifty100.db", DB),
    ("D-02", "Sprint 1", "load_audit.csv", ROOT / "Output" / "load_audit.csv"),
    ("D-03", "Sprint 1", "validation_failures.csv", ROOT / "Output" / "validation_failures.csv"),
    ("D-04", "Sprint 1", "exploratory_queries.sql", ROOT / "Notebooks" / "exploratory_queries.sql"),
    ("D-05", "Sprint 2", "financial_ratios table", DB),
    ("D-06", "Sprint 2", "capital_allocation.csv", ROOT / "Output" / "capital_allocation.csv"),
    ("D-07", "Sprint 3", "screener_output.xlsx", ROOT / "Output" / "screener_output.xlsx"),
    ("D-08", "Sprint 3", "screener_config.yaml", ROOT / "Script" / "config" / "screener_config.yaml"),
    ("D-09", "Sprint 3", "peer_comparison.xlsx", ROOT / "Output" / "peer_comparison.xlsx"),
    ("D-10", "Sprint 3", "92 Radar Charts", ROOT / "reports" / "radar_charts"),
    ("D-11", "Sprint 4", "Streamlit Dashboard", ROOT / "Script" / "dashboard" / "app.py"),
    ("D-12", "Sprint 4", "valuation_summary.xlsx", ROOT / "Output" / "valuation_summary.xlsx"),
    ("D-13", "Sprint 5", "cashflow_intelligence.xlsx", ROOT / "Output" / "cashflow_intelligence.xlsx"),
    ("D-14", "Sprint 5", "pros_cons_generated.csv", ROOT / "Output" / "pros_cons_generated.csv"),
    ("D-15", "Sprint 5", "analysis_parsed.csv", ROOT / "Output" / "analysis_parsed.csv"),
    ("D-16", "Sprint 5", "92 Company Tearsheets", ROOT / "reports" / "tearsheets"),
    ("D-17", "Sprint 5", "11 Sector Reports", ROOT / "reports" / "sector"),
    ("D-18", "Sprint 5", "Portfolio Summary PDF", ROOT / "reports" / "portfolio"),
    ("D-19", "Sprint 6", "cluster_labels.csv", ROOT / "Output" / "cluster_labels.csv"),
    ("D-20", "Sprint 6", "FastAPI Server", ROOT / "Script" / "api" / "main.py"),
    ("D-21", "Sprint 6", "pytest_report.html", ROOT / "reports" / "pytest_report.html"),
    ("D-22", "Sprint 6", "analyst_guide.pdf", ROOT / "docs" / "analyst_guide.pdf"),
    ("D-23", "Sprint 6", "acceptance_checklist.pdf", ROOT / "docs" / "acceptance_checklist.pdf"),
]


def check_file(path):
    return path.exists() and path.is_file() and path.stat().st_size > 0


def check_directory(path):
    return path.exists() and path.is_dir()


def check_database():
    if not DB.exists():
        return False, "Database missing"

    try:
        conn = sqlite3.connect(str(DB))

        integrity = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        tables = {
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            )
        }

        if integrity != "ok":
            conn.close()
            return False, f"SQLite integrity = {integrity}"

        if "financial_ratios" not in tables:
            conn.close()
            return False, "financial_ratios table missing"

        rows = conn.execute(
            "SELECT COUNT(*) FROM financial_ratios"
        ).fetchone()[0]

        conn.close()

        if rows <= 0:
            return False, "financial_ratios is empty"

        return True, f"SQLite OK; financial_ratios rows={rows}"

    except Exception as exc:
        return False, str(exc)


def check_directory_content(path):
    if not check_directory(path):
        return False, "Directory missing"

    files = [
        p for p in path.rglob("*")
        if p.is_file()
    ]

    if len(files) == 0:
        return False, "Directory empty"

    return True, f"{len(files)} files"


def run_check(item, sprint, name, path):
    if item == "D-01":
        return check_database()

    if item == "D-05":
        return check_database()

    if path.is_dir():
        return check_directory_content(path)

    if check_file(path):
        return True, f"{path.stat().st_size:,} bytes"

    return False, "Missing or empty"


def main():
    print("=" * 80)
    print("N100 FINANCIAL INTELLIGENCE PLATFORM")
    print("SPRINT 6 — FINAL 23-ITEM ACCEPTANCE CHECK")
    print("=" * 80)
    print(f"Repository: {ROOT}")
    print()

    results = []

    for item, sprint, name, path in CHECKS:
        passed, detail = run_check(item, sprint, name, path)

        status = "PASS" if passed else "FAIL"

        results.append(
            {
                "ID": item,
                "Sprint": sprint,
                "Deliverable": name,
                "Location": str(path.relative_to(ROOT)),
                "Status": status,
                "Detail": detail,
            }
        )

        print(
            f"[{status:4}] "
            f"{item} | "
            f"{sprint} | "
            f"{name} | "
            f"{detail}"
        )

    df = pd.DataFrame(results)

    output = ROOT / "Output" / "sprint6_acceptance.csv"
    df.to_csv(output, index=False)

    passed = int((df["Status"] == "PASS").sum())
    total = len(df)

    print()
    print("=" * 80)
    print(f"PASSED: {passed}/{total}")
    print(f"REPORT: {output}")
    print("=" * 80)

    if passed == 23:
        print("SPRINT 6 ACCEPTANCE: PASS")
        print("ALL 23 DELIVERABLES ARE COMPLETE.")
        return 0

    failed = df[df["Status"] == "FAIL"]

    print("SPRINT 6 ACCEPTANCE: FAIL")
    print()
    print("FAILED ITEMS:")
    print(failed.to_string(index=False))

    return 1


if __name__ == "__main__":
    sys.exit(main())