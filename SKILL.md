---
name: DOR - Distribution of Returns & Seasonality
description: Proceso estandarizado para calcular la distribución de retornos Open-to-Close y patrones de estacionalidad (mensual/diaria) de activos financieros. Genera tablas de frecuencia, estadísticas descriptivas, histogramas, sigma bands y gráficos de estacionalidad.
---

# DOR - Distribution of Returns

## Propósito

Calcular la distribución de retornos **Open-to-Close (O2C)** de cualquier activo financiero, generando:

1. **Tabla de distribución de frecuencias** con bins de 0.50%
2. **Estadísticas descriptivas** (media, std, curtosis, asimetría, etc.)
3. **Histograma** con barras rojo/verde
4. **Tabla de sigma bands** (0.5σ, 1σ, 1.5σ, 2σ) con conteo real vs distribución Gaussiana teórica

Todo calculado para **4 periodos estándar**: 2005-2025, 2010-2025, 2015-2025 y 2020-2025.

## Ubicación del Proyecto

```
c:\Users\julia\OneDrive\Documentos\Code\Skill DOR Long Term
```

## Ejecución Estándar

### Análisis multi-periodo (COMANDO PRINCIPAL)

```bash
cd "c:\Users\julia\OneDrive\Documentos\Code\Skill DOR Long Term"
py o2c_periods.py --asset NQ
```

Esto genera:
- **Reporte en consola**: Tablas de distribución + estadísticas + sigma bands para cada periodo
- **Charts PNG** en `output/charts/`: Una imagen por periodo con tabla, histograma y sigma bands

Para otro activo:
```bash
py o2c_periods.py --asset ES
py o2c_periods.py --asset SPY
py o2c_periods.py --asset QQQ
```

### Análisis completo con reportes Excel

```bash
py main.py --asset NQ --years 10
```

Genera reportes Excel/texto en `output/reports/` y gráficos adicionales en `output/charts/`.

### Auditoría del sistema

```bash
py audit.py
```

Verifica que todos los cálculos son correctos contra cálculos manuales independientes.

### Análisis de Estacionalidad (Seasonality)

```bash
py research_seasonality.py --asset NQ --month 2
```

Analiza patrones estacionales de largo plazo:
- **Monthly Seasonality**: Retorno promedio y hit rate (% positivo) por mes.
- **Daily Seasonality**: Desempeño acumulado promedio por día de trading para un mes específico (ej. Febrero).

Activos recomendados para estacionalidad de largo plazo:
- `GSPC` (S&P 500 desde 1928)
- `NQ` (Futuros Nasdaq 100 desde 2000)


## Activos Configurados

| Activo | Key | Yahoo Symbol |
|--------|-----|-------------|
| NASDAQ 100 E-mini Futures | `NQ` | `NQ=F` |
| S&P 500 E-mini Futures | `ES` | `ES=F` |
| SPDR S&P 500 ETF | `SPY` | `SPY` |
| Invesco QQQ Trust | `QQQ` | `QQQ` |

### Agregar un nuevo activo

Editar `config/assets.py`:

```python
ASSETS["SYMBOL"] = AssetConfig(
    name="Nombre del Activo",
    yahoo_symbol="YAHOO_SYMBOL",
    asset_class=AssetClass.FUTURES,  # o EQUITY, FOREX, CRYPTO
    description="Descripción",
    trading_days_per_year=252,  # 365 para crypto
    currency="USD"
)
```

## Metodología de Cálculos

### Retorno Open-to-Close (Simple Return)

```
O2C = (Close - Open) / Open
```

**¿Por qué simple return y no log return?**
- Para movimientos < 3% (95% de los días) la diferencia es despreciable
- Simple return es más intuitivo: "el activo subió 1%"
- Consistente con la metodología del archivo NQ DOR PRO
- **Verificado por auditoría**: el archivo Excel usa simple returns (confirmado)

### Tabla de Distribución de Frecuencias

- Bins de **0.50%** desde -3.00% hasta +3.00%
- Primer bin: "Menor de -3%"
- Último bin: "y mayor..." (> +3%)
- Columnas: Intervalo, Clase, Frecuencia, Rango, Probabilidad, Acumulado
- **Verificado**: Suma de frecuencias = total observaciones, acumulado = 100%

### Estadísticas Descriptivas

| Métrica | Fórmula | Notas |
|---------|---------|-------|
| **Media** | Σ(returns) / n | Retorno promedio |
| **Error típico** | std / √n | Error estándar de la media |
| **Mediana** | Percentil 50 | Valor central |
| **Desviación estándar** | √(Σ(r - μ)² / (n-1)) | Muestral con ddof=1 |
| **Varianza** | std² | |
| **Curtosis** | Cuarto momento - 3 | Exceso de curtosis |
| **Coef. de asimetría** | Tercer momento estandarizado | Skewness |
| **Rango** | Max - Min | |

### Sigma Bands

```
Superior = Mean + n × Std
Inferior = Mean - n × Std
```

Para n = 0.5, 1.0, 1.5, 2.0

Se calcula:
- **Cuenta**: Número de observaciones dentro del rango [Inferior, Superior]
- **% Cuenta**: Cuenta / Total × 100
- **% Dist Gauss**: Porcentaje teórico de una distribución normal

| Sigma | % Gaussiano Teórico |
|-------|-------------------|
| 0.5σ | 38.29% |
| 1.0σ | 68.27% |
| 1.5σ | 86.64% |
| 2.0σ | 95.45% |

**Nota**: Los valores puros de std dev son perfectamente proporcionales (1σ = 2 × 0.5σ). Las sigma bands (mean ± n×std) pueden parecer no proporcionales cuando la media ≠ 0.

### Upside / Downside

```python
positive = o2c[o2c > 0]    # Días positivos
negative = o2c[o2c < 0]    # Días negativos

upside_mean = positive.mean()
upside_std = positive.std()        # ddof=1

downside_mean = negative.mean()
downside_std = abs(negative).std() # ddof=1 sobre valores absolutos

vol_asymmetry = downside_std / upside_std
# > 1.0 = downside más volátil (típico en equity indices)
# < 1.0 = upside más volátil
```

## Periodos Estándar

| Periodo | Descripción |
|---------|-------------|
| 2005-2025 | Muestra completa (~20 años) |
| 2010-2025 | Post-crisis financiera |
| 2015-2025 | Última década |
| 2020-2025 | Periodo reciente (incluye COVID) |

## Resultados de Referencia (NQ)

```
Metrica               2005-2025     2010-2025     2015-2025     2020-2025
--------------------------------------------------------------------------------
Observaciones             5,290         4,024         2,766         1,510

Media                  +0.0571%      +0.0696%      +0.0743%      +0.0736%
Std Dev                 1.3437%       1.2679%       1.3516%       1.5600%

UPSIDE
  Cantidad                54.8%         55.5%         55.1%         54.3%
  Media                +0.8838%      +0.8528%      +0.9079%      +1.0724%
  Std Dev               0.9501%       0.8781%       0.9525%       1.1053%

DOWNSIDE
  Cantidad                44.9%         44.4%         44.8%         45.7%
  Media                -0.9508%      -0.9105%      -0.9509%      -1.1133%
  Std Dev               1.0341%       0.9647%       1.0265%       1.1313%

Vol Asym (D/U)          1.0884x       1.0986x       1.0777x       1.0236x
```

**Observaciones clave:**
- NQ tiene sesgo alcista consistente (~55% de días positivos en todos los periodos)
- Downside siempre es más volátil que upside (Vol Asym > 1x)
- Periodo 2020-2025 tiene mayor std (1.56%) por efecto COVID
- Los % reales dentro de sigma bands siempre exceden el % Gaussiano (curtosis > 0, colas pesadas)

## Estructura del Proyecto

```
Skill DOR Long Term/
├── o2c_periods.py          # SCRIPT PRINCIPAL - Análisis multi-periodo
├── research_seasonality.py # SCRIPT SEASONALITY - Análisis estacional
├── main.py                 # Análisis completo con reportes Excel/charts
├── audit.py                # Auditoría exhaustiva de cálculos
├── audit_seasonality.py    # Auditoría de cálculos de estacionalidad
├── analyze_spec.py         # Análisis del archivo Excel original
├── verify_results.py       # Comparación framework vs Excel
├── SKILL.md                # Esta documentación
├── SKILL_SEASONALITY.md    # Documentación específica de estacionalidad
├── SKILL_WEEKLY_FRACTAL_STRATEGY.md # Estrategia Fractal Semanal (D1-D2)
├── requirements.txt        # Dependencias Python
├── NQ DOR PRO - SPEC.xlsx  # Archivo Excel de referencia
├── config/
│   ├── assets.py           # Configuración de activos
│   └── timeframes.py       # Configuración de timeframes
├── src/
│   ├── data/
│   │   └── data_loader.py  # Descarga de Yahoo Finance
│   ├── returns/
│   │   └── returns_calculator.py  # Cálculo de retornos
│   ├── distributions/
│   │   └── distribution_analyzer.py  # Análisis estadístico
│   ├── seasonality/        # NUEVO MODULO
│   │   ├── seasonality_calculator.py
│   │   └── seasonality_visualizer.py
│   ├── volatility/
│   │   └── volatility_calculator.py  # Estimadores de volatilidad
│   ├── visualization/
│   │   └── visualizer.py   # Gráficos matplotlib
│   └── reports/
│       └── report_generator.py  # Reportes Excel/texto
└── output/
    ├── charts/             # PNGs generados
    └── reports/            # Excel y texto generados
```

## Dependencias

```
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.36
scipy>=1.11.0
matplotlib>=3.7.0
seaborn>=0.12.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
```

## Notas Importantes

1. **Se usa `std(ddof=1)`** - Desviación estándar muestral con corrección de Bessel
2. **Simple returns** - No logarítmicos, verificado contra archivo NQ DOR PRO
3. **Open-to-Close** - Captura solo el movimiento intradía, sin gaps overnight
4. **Datos de Yahoo Finance** - Puede haber ligeras diferencias vs otras fuentes en OHLC de futuros (< 0.01% en std)
5. **Vol Asymmetry > 1** es lo típico para índices equity (las caídas son más volátiles que las subidas)
6. **Curtosis > 0** (leptocúrtica) es lo típico — más datos caen dentro de las sigma bands que lo predicho por Gauss
