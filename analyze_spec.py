import pandas as pd
import numpy as np

filepath = r'c:\Users\julia\OneDrive\Documentos\Code\Skill DOR Long Term\NQ DOR PRO - SPEC.xlsx'
df = pd.read_excel(filepath)

print("=" * 60)
print("ANALISIS DEL ARCHIVO NQ DOR PRO - SPEC.xlsx")
print("=" * 60)

# O2C = Open to Close returns
o2c = df["O2C"].dropna()

date_col = df["Date"]
print("Periodo: {} a {}".format(date_col.min(), date_col.max()))
print("Observaciones: {:,}".format(len(o2c)))
print()

# Estadisticas generales O2C
print("OPEN TO CLOSE (O2C) - DEL ARCHIVO")
print("-" * 40)
print("  Media:          {:+.4f}%".format(o2c.mean() * 100))
print("  Desv Estandar:  {:.4f}%".format(o2c.std() * 100))
print("  Minimo:         {:.4f}%".format(o2c.min() * 100))
print("  Maximo:         {:+.4f}%".format(o2c.max() * 100))
print()

# Separar positivos y negativos
pos = o2c[o2c > 0]
neg = o2c[o2c < 0]

print("UPSIDE (O2C > 0)")
print("-" * 40)
print("  Cantidad:       {:,} ({:.1f}%)".format(len(pos), 100 * len(pos) / len(o2c)))
print("  Media:          {:+.4f}%".format(pos.mean() * 100))
print("  Desv Estandar:  {:.4f}%".format(pos.std() * 100))
print()

print("DOWNSIDE (O2C < 0)")
print("-" * 40)
print("  Cantidad:       {:,} ({:.1f}%)".format(len(neg), 100 * len(neg) / len(o2c)))
print("  Media:          {:.4f}%".format(neg.mean() * 100))
print("  Desv Estandar:  {:.4f}%".format(np.abs(neg).std() * 100))
print()

print("ASIMETRIA DE VOLATILIDAD")
print("-" * 40)
upside_std = pos.std()
downside_std = np.abs(neg).std()
ratio = downside_std / upside_std
print("  Upside Std:     {:.4f}%".format(upside_std * 100))
print("  Downside Std:   {:.4f}%".format(downside_std * 100))
print("  Ratio Down/Up:  {:.4f}x".format(ratio))
print()

# H2L = High to Low
h2l = df["H2L"].dropna()
print("HIGH TO LOW (H2L)")
print("-" * 40)
print("  Media:          {:.4f}%".format(h2l.mean() * 100))
print("  Desv Estandar:  {:.4f}%".format(h2l.std() * 100))
print("  Minimo:         {:.4f}%".format(h2l.min() * 100))
print("  Maximo:         {:.4f}%".format(h2l.max() * 100))
print()

# Ver la tabla de distribucion que tiene el archivo
print("TABLA DE DISTRIBUCION DEL ARCHIVO")
print("-" * 40)
tabla = df[["OPEN TO CLOSE", "Unnamed: 10", "Unnamed: 11", "Unnamed: 12", "Unnamed: 13", "Unnamed: 14"]].dropna()
tabla.columns = ["Intervalo", "Clase", "Frecuencia", "Rango", "Probabilidad", "Acumulado"]
print(tabla.to_string(index=False))
print()

# Verificar: recalcular O2C desde precios
print("VERIFICACION: Recalculo O2C desde OHLC")
print("-" * 40)
recalc_o2c = np.log(df["Close"] / df["Open"])
diff = (recalc_o2c - df["O2C"]).dropna()
print("  Max diferencia vs archivo: {:.8f}".format(diff.abs().max()))
print("  Son iguales (log returns): {}".format(diff.abs().max() < 1e-6))

# Verificar si usan simple returns
recalc_simple = (df["Close"] - df["Open"]) / df["Open"]
diff_simple = (recalc_simple - df["O2C"]).dropna()
print("  Max diferencia (simple ret): {:.8f}".format(diff_simple.abs().max()))
print("  Son simple returns: {}".format(diff_simple.abs().max() < 1e-6))
