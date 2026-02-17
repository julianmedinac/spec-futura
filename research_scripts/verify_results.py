"""Verify framework results match the user's NQ DOR PRO - SPEC.xlsx"""
import sys
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from src.data.data_loader import download_asset_data
from src.returns.returns_calculator import ReturnsCalculator

# Load user's file
filepath = r'NQ DOR PRO - SPEC.xlsx'
user_df = pd.read_excel(filepath)
user_o2c = user_df["O2C"].dropna()
user_pos = user_o2c[user_o2c > 0]
user_neg = user_o2c[user_o2c < 0]

# Run framework (download same period as user's file: 2005 to 2025-11)
print("Descargando datos NQ desde Yahoo Finance...")
data = download_asset_data('NQ', start_date='2005-01-01', end_date='2025-11-10')
calc = ReturnsCalculator(data)
fw_o2c = calc.open_to_close_returns()
fw_pos = fw_o2c[fw_o2c > 0]
fw_neg = fw_o2c[fw_o2c < 0]

print()
print("=" * 70)
print("COMPARACION: Tu archivo vs Framework DOR")
print("=" * 70)
print()
print("{:<30} {:>18} {:>18}".format("Metrica", "Tu Archivo", "Framework DOR"))
print("-" * 70)
print("{:<30} {:>18,} {:>18,}".format("Observaciones", len(user_o2c), len(fw_o2c)))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Media O2C", user_o2c.mean()*100, fw_o2c.mean()*100))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Desv Estandar", user_o2c.std()*100, fw_o2c.std()*100))
print()
print("{:<30} {:>18} {:>18}".format("--- UPSIDE ---", "", ""))
print("{:<30} {:>18,} {:>18,}".format("Cantidad", len(user_pos), len(fw_pos)))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Media", user_pos.mean()*100, fw_pos.mean()*100))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Desv Estandar", user_pos.std()*100, fw_pos.std()*100))
print()
print("{:<30} {:>18} {:>18}".format("--- DOWNSIDE ---", "", ""))
print("{:<30} {:>18,} {:>18,}".format("Cantidad", len(user_neg), len(fw_neg)))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Media", user_neg.mean()*100, fw_neg.mean()*100))
print("{:<30} {:>18.4f}% {:>18.4f}%".format("Desv Estandar", np.abs(user_neg).std()*100, np.abs(fw_neg).std()*100))
print()
print("{:<30} {:>18} {:>18}".format("--- RATIO ---", "", ""))
user_ratio = np.abs(user_neg).std() / user_pos.std()
fw_ratio = np.abs(fw_neg).std() / fw_pos.std()
print("{:<30} {:>18.4f}x {:>18.4f}x".format("Down/Up Ratio", user_ratio, fw_ratio))
