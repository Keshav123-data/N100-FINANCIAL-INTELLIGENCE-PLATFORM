import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent

RAW_BS = ROOT / "Data" / "raw" / "balancesheet.xlsx"
PROCESSED_BS = ROOT / "Data" / "processed" / "balancesheet.csv"

RAW_PL = ROOT / "Data" / "raw" / "profitandloss.xlsx"
PROCESSED_PL = ROOT / "Data" / "processed" / "profitandloss.csv"


def inspect_file(path, name):
    print("\n" + "=" * 100)
    print(name)
    print("=" * 100)
    print("FILE:", path)

    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nShape:")
    print(df.shape)

    return df


# ---------------------------------------------------------
# BALANCE SHEET
# ---------------------------------------------------------

raw_bs = inspect_file(
    RAW_BS,
    "RAW BALANCE SHEET"
)

processed_bs = inspect_file(
    PROCESSED_BS,
    "PROCESSED BALANCE SHEET"
)


# ---------------------------------------------------------
# BEL RAW BALANCE SHEET
# ---------------------------------------------------------

print("\n" + "=" * 100)
print("BEL — RAW BALANCE SHEET")
print("=" * 100)

bel_raw = raw_bs[
    raw_bs.astype(str)
    .apply(
        lambda row: row.str.contains(
            "BEL",
            case=False,
            na=False
        ).any(),
        axis=1
    )
]

print(bel_raw.tail(15).to_string(index=False))


# ---------------------------------------------------------
# BEL PROCESSED BALANCE SHEET
# ---------------------------------------------------------

print("\n" + "=" * 100)
print("BEL — PROCESSED BALANCE SHEET")
print("=" * 100)

if "company_id" in processed_bs.columns:

    bel_processed = processed_bs[
        processed_bs["company_id"]
        .astype(str)
        .str.upper()
        .eq("BEL")
    ]

else:

    bel_processed = processed_bs[
        processed_bs.astype(str)
        .apply(
            lambda row: row.str.contains(
                "BEL",
                case=False,
                na=False
            ).any(),
            axis=1
        )
    ]

print(bel_processed.tail(15).to_string(index=False))


# ---------------------------------------------------------
# PROFIT AND LOSS
# ---------------------------------------------------------

raw_pl = inspect_file(
    RAW_PL,
    "RAW PROFIT AND LOSS"
)

processed_pl = inspect_file(
    PROCESSED_PL,
    "PROCESSED PROFIT AND LOSS"
)


print("\n" + "=" * 100)
print("BEL — PROCESSED PROFIT AND LOSS")
print("=" * 100)

bel_pl = processed_pl[
    processed_pl["company_id"]
    .astype(str)
    .str.upper()
    .eq("BEL")
]

print(bel_pl.tail(15).to_string(index=False))


print("\n" + "=" * 100)
print("SOURCE INSPECTION COMPLETE")
print("=" * 100)