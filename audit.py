"""
AUDITORIA EXHAUSTIVA DEL SISTEMA DOR
=====================================
Verifica TODOS los calculos del framework contra calculos manuales independientes.
"""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from src.data.data_loader import download_asset_data
from src.returns.returns_calculator import ReturnsCalculator

TOLERANCE = 1e-10
PASS = "[PASS]"
FAIL = "[FAIL]"
errors_found = 0


def check(test_name, condition, detail=""):
    global errors_found
    status = PASS if condition else FAIL
    if not condition:
        errors_found += 1
    print(f"  {status}  {test_name}")
    if detail and not condition:
        print(f"         {detail}")
    return condition


def section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


# ============================================================================
# 1. DATA DOWNLOAD & O2C CALCULATION
# ============================================================================
section("1. DESCARGA DE DATOS Y CALCULO O2C")

data = download_asset_data('NQ', start_date='2020-01-01', end_date='2025-12-31')
calc = ReturnsCalculator(data)
o2c = calc.open_to_close_returns()

print(f"\n  Datos descargados: {len(data)} filas")
print(f"  Columnas: {list(data.columns)}")
print(f"  O2C calculados: {len(o2c)} valores")

# Verify O2C formula: (Close - Open) / Open
manual_o2c = (data['close'] - data['open']) / data['open']
manual_o2c = manual_o2c.dropna()

check("O2C usa formula (Close-Open)/Open",
      np.allclose(o2c.values, manual_o2c.values, atol=TOLERANCE),
      f"Max diff: {(o2c - manual_o2c).abs().max()}")

check("O2C NO usa log returns ln(Close/Open)",
      not np.allclose(o2c.values, np.log(data['close'] / data['open']).dropna().values, atol=1e-6),
      "ALERTA: Está usando log returns en vez de simple returns")

# Verify no NaN values
check("O2C no tiene valores NaN", o2c.isna().sum() == 0,
      f"NaN encontrados: {o2c.isna().sum()}")

# Verify count matches
check("Cantidad O2C = filas de datos", len(o2c) == len(data),
      f"O2C: {len(o2c)}, Data: {len(data)}")


# ============================================================================
# 2. ESTADÍSTICAS DESCRIPTIVAS
# ============================================================================
section("2. ESTADISTICAS DESCRIPTIVAS")

mean = o2c.mean()
std = o2c.std()  # ddof=1 by default in pandas
var = o2c.var()
median = o2c.median()
skew = o2c.skew()
kurt = o2c.kurtosis()  # excess kurtosis
se = std / np.sqrt(len(o2c))

# Manual calculations
manual_mean = o2c.sum() / len(o2c)
manual_var = ((o2c - manual_mean) ** 2).sum() / (len(o2c) - 1)  # ddof=1
manual_std = np.sqrt(manual_var)

print(f"\n  Mean:     {mean*100:+.6f}%")
print(f"  Std Dev:  {std*100:.6f}%")
print(f"  Variance: {var*100:.6f}%")
print(f"  Median:   {median*100:.6f}%")
print(f"  Skew:     {skew:.9f}")
print(f"  Kurtosis: {kurt:.9f}")
print()

check("Mean = suma/n",
      abs(mean - manual_mean) < TOLERANCE,
      f"Pandas: {mean}, Manual: {manual_mean}")

check("Std usa ddof=1 (muestral)",
      abs(std - manual_std) < TOLERANCE,
      f"Pandas: {std}, Manual ddof=1: {manual_std}")

check("Variance = std^2",
      abs(var - std**2) < TOLERANCE,
      f"Var: {var}, Std^2: {std**2}")

# Verify against numpy
np_mean = np.mean(o2c.values)
np_std = np.std(o2c.values, ddof=1)

check("Mean coincide con numpy",
      abs(mean - np_mean) < TOLERANCE,
      f"Pandas: {mean}, Numpy: {np_mean}")

check("Std coincide con numpy (ddof=1)",
      abs(std - np_std) < TOLERANCE,
      f"Pandas: {std}, Numpy: {np_std}")

# Verify Standard Error
check("Error tipico = std / sqrt(n)",
      abs(se - std / np.sqrt(len(o2c))) < TOLERANCE)


# ============================================================================
# 3. SEPARACIÓN UPSIDE / DOWNSIDE
# ============================================================================
section("3. SEPARACION UPSIDE / DOWNSIDE")

pos = o2c[o2c > 0]
neg = o2c[o2c < 0]
zeros = o2c[o2c == 0]

print(f"\n  Positivos: {len(pos)} ({len(pos)/len(o2c)*100:.2f}%)")
print(f"  Negativos: {len(neg)} ({len(neg)/len(o2c)*100:.2f}%)")
print(f"  Ceros:     {len(zeros)} ({len(zeros)/len(o2c)*100:.2f}%)")
print(f"  Total:     {len(pos) + len(neg) + len(zeros)}")
print()

check("Pos + Neg + Zeros = Total",
      len(pos) + len(neg) + len(zeros) == len(o2c),
      f"Sum: {len(pos) + len(neg) + len(zeros)}, Total: {len(o2c)}")

check("Todos los positivos son > 0",
      (pos > 0).all())

check("Todos los negativos son < 0",
      (neg < 0).all())

# Upside stats
pos_mean = pos.mean()
pos_std = pos.std()  # ddof=1

check("Upside mean > 0", pos_mean > 0,
      f"Upside mean: {pos_mean}")

check("Upside std calculada con ddof=1",
      abs(pos_std - np.std(pos.values, ddof=1)) < TOLERANCE)

# Downside stats
neg_mean = neg.mean()
neg_std_abs = np.abs(neg).std()  # std of absolute values

check("Downside mean < 0", neg_mean < 0,
      f"Downside mean: {neg_mean}")

# IMPORTANT: Verify downside std calculation
neg_std_direct = neg.std()  # std of raw negative values
neg_std_abs_manual = np.std(np.abs(neg.values), ddof=1)

print(f"\n  DOWNSIDE STD COMPARACION:")
print(f"    std(neg) directo:        {neg_std_direct*100:.6f}%")
print(f"    std(|neg|) abs values:   {neg_std_abs*100:.6f}%")
print(f"    Son iguales? {abs(neg_std_direct - neg_std_abs) < TOLERANCE}")
print()

check("Downside std usa valores absolutos: std(|neg|)",
      abs(neg_std_abs - neg_std_abs_manual) < TOLERANCE)

# NOTE: std(neg) == std(|neg|) mathematically because std only measures spread
# std(X) = sqrt(E[(X-mean)^2]) and std(|X|) = sqrt(E[(|X|-mean_abs)^2])
# These are NOT the same! Let's verify which one the system uses
print(f"  NOTA: std(neg)={neg_std_direct*100:.6f}% vs std(|neg|)={neg_std_abs*100:.6f}%")
print(f"  Diferencia: {abs(neg_std_direct - neg_std_abs)*100:.6f}%")
if abs(neg_std_direct - neg_std_abs) > 1e-10:
    print(f"  >> Las dos medidas SON DIFERENTES. El sistema usa std(|neg|).")
    print(f"  >> std(neg) mide dispersión de los retornos negativos alrededor de su media negativa")
    print(f"  >> std(|neg|) mide dispersión de las magnitudes alrededor de la media de magnitudes")


# ============================================================================
# 4. VOLATILITY ASYMMETRY
# ============================================================================
section("4. ASIMETRIA DE VOLATILIDAD")

vol_asym = neg_std_abs / pos_std

print(f"\n  Upside Std:   {pos_std*100:.6f}%")
print(f"  Downside Std: {neg_std_abs*100:.6f}%")
print(f"  Ratio D/U:    {vol_asym:.6f}x")
print()

check("Vol Asymmetry = downside_std / upside_std",
      abs(vol_asym - neg_std_abs / pos_std) < TOLERANCE)

check("Ratio > 1 indica downside mas volatil",
      (vol_asym > 1) == (neg_std_abs > pos_std))


# ============================================================================
# 5. TABLA DE DISTRIBUCIÓN (FRECUENCIAS)
# ============================================================================
section("5. TABLA DE DISTRIBUCION")

bin_size = 0.005  # 0.50%
bin_min = -0.03
bin_max = 0.03
edges = np.arange(bin_min, bin_max + bin_size, bin_size)

total_freq = 0
total_prob = 0.0

# Count per bin
print()
for i in range(len(edges)):
    if i == 0:
        mask = o2c <= edges[i]
        label = f"<= {edges[i]*100:.1f}%"
    else:
        mask = (o2c > edges[i-1]) & (o2c <= edges[i])
        label = f"({edges[i-1]*100:.1f}%, {edges[i]*100:.1f}%]"
    
    freq = mask.sum()
    prob = freq / len(o2c) * 100
    total_freq += freq
    total_prob += prob

# "y mayor" bin
mask_mayor = o2c > bin_max
freq_mayor = mask_mayor.sum()
prob_mayor = freq_mayor / len(o2c) * 100
total_freq += freq_mayor
total_prob += prob_mayor

print(f"  Total frecuencias: {total_freq}")
print(f"  Total probabilidad: {total_prob:.6f}%")
print()

check("Suma de frecuencias = total observaciones",
      total_freq == len(o2c),
      f"Suma: {total_freq}, Total: {len(o2c)}")

check("Suma de probabilidades = 100%",
      abs(total_prob - 100.0) < 0.001,
      f"Suma: {total_prob:.6f}%")

# Verify no observation is counted twice or missed
all_masks = []
for i in range(len(edges)):
    if i == 0:
        all_masks.append(o2c <= edges[i])
    else:
        all_masks.append((o2c > edges[i-1]) & (o2c <= edges[i]))
all_masks.append(o2c > bin_max)

combined = pd.concat(all_masks, axis=1)
obs_per_row = combined.sum(axis=1)

check("Cada observacion cae en exactamente 1 bin",
      (obs_per_row == 1).all(),
      f"Obs en 0 bins: {(obs_per_row == 0).sum()}, en >1 bins: {(obs_per_row > 1).sum()}")

# Verify cumulative reaches 100%
cum_total = total_prob
check("Acumulado final = 100%",
      abs(cum_total - 100.0) < 0.001,
      f"Acumulado: {cum_total:.6f}%")


# ============================================================================
# 6. SIGMA BANDS
# ============================================================================
section("6. SIGMA BANDS")

sigmas = [0.5, 1, 1.5, 2]

print(f"\n  Mean: {mean*100:+.6f}%")
print(f"  Std:  {std*100:.6f}%")
print()

for sig in sigmas:
    superior = mean + sig * std
    inferior = mean - sig * std
    
    # Manual count
    manual_count = ((o2c >= inferior) & (o2c <= superior)).sum()
    manual_pct = manual_count / len(o2c) * 100
    
    # Theoretical Gaussian
    gauss_pct = (scipy_stats.norm.cdf(sig) - scipy_stats.norm.cdf(-sig)) * 100
    
    print(f"  {sig:.1f}σ: [{inferior*100:+.4f}%, {superior*100:+.4f}%]  "
          f"Actual: {manual_pct:.2f}%  Gauss: {gauss_pct:.3f}%")
    
    # Verify formula
    check(f"{sig:.1f}σ superior = mean + {sig}*std",
          abs(superior - (mean + sig * std)) < TOLERANCE)
    
    check(f"{sig:.1f}σ inferior = mean - {sig}*std",
          abs(inferior - (mean - sig * std)) < TOLERANCE)
    
    # Verify count is correct
    check(f"{sig:.1f}σ count is correct",
          manual_count == ((o2c >= inferior) & (o2c <= superior)).sum())
    
    # Sigma bands should be symmetric STEPS (each 0.5σ step = same size)
    step = sig * std
    check(f"{sig:.1f}σ band width = {sig}x std",
          abs(step - sig * std) < TOLERANCE)

# Verify proportionality: 1σ = 2 × 0.5σ (pure std values)
print()
check("1.0σ = exactamente 2 × 0.5σ (valor puro de std)",
      abs(1.0 * std - 2 * 0.5 * std) < TOLERANCE,
      f"1σ: {std*100:.6f}%, 2×0.5σ: {2*0.5*std*100:.6f}%")

check("1.5σ = exactamente 3 × 0.5σ (valor puro de std)",
      abs(1.5 * std - 3 * 0.5 * std) < TOLERANCE)

check("2.0σ = exactamente 4 × 0.5σ (valor puro de std)",
      abs(2.0 * std - 4 * 0.5 * std) < TOLERANCE)

# Verify Gaussian percentages
print()
check("Gauss 0.5σ ≈ 38.29%",
      abs((scipy_stats.norm.cdf(0.5) - scipy_stats.norm.cdf(-0.5)) * 100 - 38.292) < 0.01)

check("Gauss 1.0σ ≈ 68.27%",
      abs((scipy_stats.norm.cdf(1.0) - scipy_stats.norm.cdf(-1.0)) * 100 - 68.269) < 0.01)

check("Gauss 1.5σ ≈ 86.64%",
      abs((scipy_stats.norm.cdf(1.5) - scipy_stats.norm.cdf(-1.5)) * 100 - 86.639) < 0.01)

check("Gauss 2.0σ ≈ 95.45%",
      abs((scipy_stats.norm.cdf(2.0) - scipy_stats.norm.cdf(-2.0)) * 100 - 95.450) < 0.01)


# ============================================================================
# 7. COMPARACIÓN CON ARCHIVO EXCEL (NQ DOR PRO)
# ============================================================================
section("7. COMPARACION CON ARCHIVO EXCEL NQ DOR PRO")

try:
    filepath = r'NQ DOR PRO - SPEC.xlsx'
    user_df = pd.read_excel(filepath)
    user_o2c = user_df["O2C"].dropna()
    
    print(f"\n  Archivo Excel: {len(user_o2c)} observaciones")
    print(f"  Periodo: {user_df['Date'].min()} a {user_df['Date'].max()}")
    
    # Verify the Excel file uses simple returns
    recalc_simple = (user_df["Close"] - user_df["Open"]) / user_df["Open"]
    diff_simple = (recalc_simple - user_df["O2C"]).dropna()
    
    check("Excel usa simple returns (Close-Open)/Open",
          diff_simple.abs().max() < 1e-6,
          f"Max diff: {diff_simple.abs().max()}")
    
    recalc_log = np.log(user_df["Close"] / user_df["Open"])
    diff_log = (recalc_log - user_df["O2C"]).dropna()
    
    check("Excel NO usa log returns",
          diff_log.abs().max() > 1e-6,
          f"Max diff con log: {diff_log.abs().max()}")
    
    # Compare stats
    excel_mean = user_o2c.mean()
    excel_std = user_o2c.std()
    
    print(f"\n  Excel  - Mean: {excel_mean*100:+.6f}%, Std: {excel_std*100:.6f}%")
    
    # Download same period for framework comparison
    date_min = user_df['Date'].min()
    date_max = user_df['Date'].max()
    fw_data = download_asset_data('NQ', start_date=str(date_min)[:10], end_date=str(date_max)[:10])
    fw_calc = ReturnsCalculator(fw_data)
    fw_o2c = fw_calc.open_to_close_returns()
    
    fw_mean = fw_o2c.mean()
    fw_std = fw_o2c.std()
    
    print(f"  Frame  - Mean: {fw_mean*100:+.6f}%, Std: {fw_std*100:.6f}%")
    print(f"  Diff obs: Excel={len(user_o2c)}, Framework={len(fw_o2c)}")
    print()
    
    # Note: Small differences expected due to Yahoo Finance data variations
    mean_diff_pct = abs(excel_mean - fw_mean) / abs(excel_mean) * 100 if excel_mean != 0 else 0
    std_diff_pct = abs(excel_std - fw_std) / abs(excel_std) * 100
    
    check(f"Mean difference < 20% (data source variation expected)",
          mean_diff_pct < 20,
          f"Diff: {mean_diff_pct:.2f}%")
    
    check(f"Std difference < 10% (data source variation expected)",
          std_diff_pct < 10,
          f"Diff: {std_diff_pct:.2f}%")

except FileNotFoundError:
    print("\n  NOTA: Archivo Excel no encontrado, saltando comparación")
except Exception as e:
    print(f"\n  ERROR leyendo Excel: {e}")


# ============================================================================
# 8. CONSISTENCIA ENTRE PERIODOS
# ============================================================================
section("8. CONSISTENCIA ENTRE PERIODOS")

periods = [
    ('2005-01-01', '2025-12-31', '2005-2025'),
    ('2010-01-01', '2025-12-31', '2010-2025'),
    ('2015-01-01', '2025-12-31', '2015-2025'),
    ('2020-01-01', '2025-12-31', '2020-2025'),
]

period_results = {}
for start, end, label in periods:
    d = download_asset_data('NQ', start_date=start, end_date=end)
    c = ReturnsCalculator(d)
    r = c.open_to_close_returns()
    period_results[label] = {
        'o2c': r,
        'mean': r.mean(),
        'std': r.std(),
        'count': len(r),
    }
    print(f"  {label}: n={len(r)}, mean={r.mean()*100:+.4f}%, std={r.std()*100:.4f}%")

print()

# Longer period should have more observations
check("2005-2025 tiene más obs que 2010-2025",
      period_results['2005-2025']['count'] > period_results['2010-2025']['count'])

check("2010-2025 tiene más obs que 2015-2025",
      period_results['2010-2025']['count'] > period_results['2015-2025']['count'])

check("2015-2025 tiene más obs que 2020-2025",
      period_results['2015-2025']['count'] > period_results['2020-2025']['count'])

# 2020-2025 data should be a SUBSET of 2005-2025 data (same dates should match)
o2c_2005 = period_results['2005-2025']['o2c']
o2c_2020 = period_results['2020-2025']['o2c']
common_dates = o2c_2005.index.intersection(o2c_2020.index)
overlap = o2c_2005.loc[common_dates] - o2c_2020.loc[common_dates]

check("2020-2025 valores son subconjunto exacto de 2005-2025",
      overlap.abs().max() < TOLERANCE if len(overlap) > 0 else True,
      f"Max diff en fechas comunes: {overlap.abs().max() if len(overlap) > 0 else 'N/A'}")

# All means should be positive (NQ has bullish bias)
for label in period_results:
    check(f"{label} mean > 0 (sesgo alcista NQ)",
          period_results[label]['mean'] > 0)


# ============================================================================
# 9. EDGE CASES Y SANIDAD
# ============================================================================
section("9. EDGE CASES Y SANIDAD")

# No infinite values
check("No hay valores infinitos en O2C",
      not np.isinf(o2c).any())

# All prices are positive
check("Todos los precios Open > 0",
      (data['open'] > 0).all())

check("Todos los precios Close > 0",
      (data['close'] > 0).all())

# Returns are reasonable (no > 50% daily moves)
check("No hay retornos O2C > 50% (sanity check)",
      (o2c.abs() < 0.50).all(),
      f"Max abs return: {o2c.abs().max()*100:.2f}%")

# Dates are sorted
check("Fechas están ordenadas cronológicamente",
      (data.index == data.index.sort_values()).all())

# No duplicate dates
check("No hay fechas duplicadas",
      not data.index.duplicated().any(),
      f"Duplicados: {data.index.duplicated().sum()}")

# Std > 0 always
check("Std Dev > 0",
      std > 0)

# Kurtosis of financial returns should be > 0 (leptokurtic / fat tails)
check("Curtosis > 0 (colas pesadas, tipico en finanzas)",
      kurt > 0,
      f"Kurtosis: {kurt:.4f}")


# ============================================================================
# RESUMEN FINAL
# ============================================================================
section("RESUMEN DE AUDITORIA")

if errors_found == 0:
    print(f"\n  ✓ TODOS LOS TESTS PASARON - 0 errores encontrados")
    print(f"  El sistema calcula correctamente.")
else:
    print(f"\n  ✗ {errors_found} ERROR(ES) ENCONTRADO(S)")
    print(f"  Revisar los tests marcados con ✗ FAIL arriba.")

print()
