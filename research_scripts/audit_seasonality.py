"""
AUDITORÍA DEL SISTEMA DE ESTACIONALIDAD (Seasonality)
=====================================================
Verifica la lógica matemática de los cálculos estacionales.
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, '.')

from src.seasonality.seasonality_calculator import SeasonalityCalculator

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

def section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

# ============================================================================
# 1. TEST CON DATA SINTÉTICA (Controlada)
# ============================================================================
section("1. TEST CON DATA SINTETICA")

# Crear 2 años de datos ficticios para Enero (Mes 1)
# Año 1: Enero tiene retornos: +1%, +1%
# Año 2: Enero tiene retornos: -1%, -1%
# Año 3: Enero tiene retornos: +2%, +0%

dates = [
    # Año 2020 (Enero)
    '2020-01-02', '2020-01-03', 
    # Año 2021 (Enero)
    '2021-01-04', '2021-01-05',
    # Año 2022 (Enero)
    '2022-01-03', '2022-01-04',
]
# Precios para generar esos retornos exactos
# R = (Close-Prev)/Prev
# 2020: Start 100. Day1 (+1%) -> 101. Day2 (+1%) -> 102.01
# 2021: Start 100. Day1 (-1%) -> 99. Day2 (-1%) -> 98.01
# 2022: Start 100. Day1 (+2%) -> 102. Day2 (0%) -> 102.0

# NOTA: SeasonalityCalculator calcula pct_change() internamente basado en 'close'.
# Necesitamos un día previo para el primer retorno, o aceptar que el primer día es NaN.
# El sistema elimina NaNs. Así que agregamos un día "dummy" previo a cada mes para que el día 1 tenga retorno.

dates_full = [
    # 2020
    '2019-12-31', '2020-01-02', '2020-01-03',
    # 2021
    '2020-12-31', '2021-01-04', '2021-01-05',
    # 2022
    '2021-12-31', '2022-01-03', '2022-01-04'
]
closes = [
    # 2020 (Retornos esperados: +1%, +1%)
    100.0, 101.0, 102.01,
    # 2021 (Retornos esperados: -1%, -1%)
    100.0, 99.0, 98.01,
    # 2022 (Retornos esperados: +2%, 0%)
    100.0, 102.0, 102.0
]

df_synthetic = pd.DataFrame({
    'close': closes
}, index=pd.to_datetime(dates_full))

calc = SeasonalityCalculator(df_synthetic)

# Forzamos recalcular los cambios porcentuales para validar
df_check = calc.data.copy()
# Los días dummies (Dec 31) no tendrán month=1, así que no entran en el filtro del mes target
# Pero el pct_change() del día 2 de Enero se calcula contra el 31 de Dic. Correcto.

print("  Data Sintética (Enero filtrado por el sistema):")
print(df_check[df_check['month'] == 1][['close', 'pct_change']])

# CALCULAMOS STATS MENSUALES
monthly_stats = calc.calculate_monthly_stats()
stats_jan = monthly_stats.loc[1]

# Validación Manual:
# Año 2020 Mes 1: Total Return = 102.01 / 100 - 1 = +2.01%
# Año 2021 Mes 1: Total Return = 98.01 / 100 - 1 = -1.99%
# Año 2022 Mes 1: Total Return = 102.0 / 100 - 1 = +2.00%
# Mean Monthly Return = (2.01% - 1.99% + 2.00%) / 3 = 2.02% / 3 = +0.6733%
# Hit Rate: 2020(+), 2021(-), 2022(+) = 2/3 = 66.66%

print(f"\n  Monthly Stats (Enero):")
print(f"    Mean Return: {stats_jan['mean_return']*100:.4f}%")
print(f"    Hit Rate:    {stats_jan['hit_rate']*100:.2f}%")

check("Monthly Mean Return Calculation", 
      abs(stats_jan['mean_return'] - (0.0201 - 0.0199 + 0.0200)/3) < 0.0001,
      f"Calculado: {stats_jan['mean_return']}, Esperado: {(0.0201 - 0.0199 + 0.0200)/3}")

check("Monthly Hit Rate Calculation",
      abs(stats_jan['hit_rate'] - 2/3) < TOLERANCE,
      f"Hit Rate: {stats_jan['hit_rate']}")


# CALCULAMOS STATS DIARIAS (Trading Day)
daily_est = calc.calculate_daily_seasonality(1)

# Validación Manual Daily Seasonality:
# Day 1 Returns:
#   2020: +1.0%
#   2021: -1.0%
#   2022: +2.0%
#   Avg Day 1 = (1 - 1 + 2)/3 = +0.6666%

# Day 2 Returns:
#   2020: +1.0%
#   2021: -1.0%
#   2022:  0.0%
#   Avg Day 2 = (1 - 1 + 0)/3 = 0.0%

# Cumulative Curve (Base 100):
#   Start = 100
#   Day 1 = 100 * (1 + 0.006666) = 100.6666
#   Day 2 = 100.6666 * (1 + 0.0) = 100.6666

print(f"\n  Daily Seasonality (Enero):")
print(daily_est)

val_day1 = daily_est.loc[1, 'level']
expected_day1 = 100 * (1 + (0.01 - 0.01 + 0.02)/3)
check("Daily Seasonality Day 1 Level",
      abs(val_day1 - expected_day1) < TOLERANCE,
      f"Day 1: {val_day1}, Expected: {expected_day1}")

val_day2 = daily_est.loc[2, 'level']
expected_day2 = val_day1 * 1.0 # Avg return day 2 is 0
check("Daily Seasonality Day 2 Level",
      abs(val_day2 - expected_day2) < TOLERANCE,
      f"Day 2: {val_day2}, Expected: {expected_day2}")


# ============================================================================
# 2. TEST LOGICA DE DATOS REALES (Sanity Check)
# ============================================================================
section("2. SANITY CHECK CON DATA GSPC (S&P 500)")

from src.data.data_loader import download_asset_data
try:
    # Usamos datos recientes para que sea rápido
    df_real = download_asset_data('GSPC', start_date='2020-01-01', end_date='2023-12-31')
    calc_real = SeasonalityCalculator(df_real)
    monthly_real = calc_real.calculate_monthly_stats()
    
    print("\n  GSPC 2020-2023 Monthly Stats:")
    print(monthly_real)
    
    # Check 1: Hit rate must be between 0 and 1
    check("Hit Rate válido (0-1)", 
          (monthly_real['hit_rate'] >= 0).all() and (monthly_real['hit_rate'] <= 1).all())
    
    # Check 2: Count should be roughly 4 (4 years of data implies ~4 occurences per month)
    # Note: data ends 2023-12-31, so 2020, 2021, 2022, 2023 = 4 years
    check("Conteo de años correcto (~4)",
          (monthly_real['count'] == 4).all(),
          f"Counts: {monthly_real['count'].unique()}")
          
    # Check 3: Trading Days ordering
    # Febrero (Month 2) max trading days should be around 19-20 usually
    daily_feb = calc_real.calculate_daily_seasonality(2)
    max_day = daily_feb.index.max()
    print(f"\n  Max Trading Day in Feb (2020-2023): {max_day}")
    
    check("Max trading days en Feb es razonable (19-21)",
          19 <= max_day <= 21,
          f"Max day: {max_day}")
    
    # Check 4: Curve starts near 100 (Day 1 level should be 100 * (1+r1))
    day1_level = daily_feb.iloc[0]['level']
    check("La curva empieza cerca de 100",
          90 < day1_level < 110)

except Exception as e:
    print(f"Error en sanity check: {e}")
    errors_found += 1

# ============================================================================
# RESUMEN
# ============================================================================
section("RESUMEN AUDITORIA SEASONALITY")
if errors_found == 0:
    print(f"  [PASS] TODOS LOS TESTS PASARON.")
else:
    print(f"  [FAIL] {errors_found} ERROR(ES) ENCONTRADOS.")
