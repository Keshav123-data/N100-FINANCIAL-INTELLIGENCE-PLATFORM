import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.screener.engine import ScreenerEngine

engine = ScreenerEngine(r"C:\Users\keshav shinde\OneDrive\Desktop\N100 FINANCIAL INTELLIGENCE PLATFORM\Script\config\screener_config.yaml")

df = pd.read_csv(r"C:\Users\keshav shinde\OneDrive\Desktop\N100 FINANCIAL INTELLIGENCE PLATFORM\Output\financial_ratios.csv")

result = engine.apply_filters(df)

print(result.head())
print(result.shape)