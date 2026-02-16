---
name: Seasonality and Statistics Research
description: Guía completa para el análisis de estacionalidad mensual y diaria, incluyendo metodología de cálculo, interpretación de Hit Rate, Peak/Bottom days y significancia estadística (T-Stat/P-Value).
---

# Seasonality & Statistical Research

## Propósito

Este módulo permite identificar patrones recurrentes en el comportamiento de activos financieros basándose en datos históricos de largo plazo. Responde preguntas clave como:
- ¿Qué meses son históricamente alcistas o bajistas?
- ¿Qué fiabilidad (Hit Rate) tienen estos movimientos?
- ¿En qué día del mes suele agotarse la tendencia (Peak/Bottom Day)?
- ¿Son estos patrones estadísticamente significativos o puro ruido?

## Ejecución del Análisis

El script principal descarga la data completa disponible en Yahoo Finance y genera todos los reportes y gráficos.

```bash
# Ejecutar para activos por defecto (GSPC, NQ)
py research_seasonality.py

# Ejecutar para un activo específico
py research_seasonality.py --asset SPY
```

**Outputs Generados:**
- `output/charts/seasonality/{ASSET}_monthly_seasonality.png`: Gráfico de barras con retornos promedio y Hit Rate.
- `output/charts/seasonality/{ASSET}_{MONTH}_daily_seasonality.png`: 12 gráficos (uno por mes) mostrando la curva de desempeño acumulado promedio día a día.

## Metodología de Cálculo

### 1. Retornos Mensuales (Monthly Stats)
- **Retorno Promedio**: Media aritmética de los retornos de cada mes $m$ a lo largo de todos los años $y$.
- **Hit Rate (Tasa de Acierto)**: Porcentaje de veces que el mes cerró positivo.
  $$ \text{Hit Rate} = \frac{\text{Años Positivos}}{\text{Total Años}} \times 100 $$
- **Significancia Estadística (T-Test)**:
  - **Hipótesis Nula ($H_0$)**: El retorno promedio del mes es 0.
  - **P-Value**: Probabilidad de obtener estos resultados por azar. Si $p < 0.05$, rechazamos $H_0$ con 95% de confianza (el patrón es real).

### 2. Estacionalidad Diaria (Daily Seasonality)
- **Agrupación**: Se alinean los meses por **Trading Day** (Día 1, Día 2... Día $N$).
- **Curva Acumulada**:
  1. Se calcula el retorno promedio para cada Día de Trading $d$.
  2. Se construye una curva base 100 compuesta.
  $$ \text{Nivel}_d = \text{Nivel}_{d-1} \times (1 + \text{Retorno Promedio}_d) $$
- **Peak / Bottom Detection**:
  - Si el mes es **Alcista** (Cierre > Apertura): Se identifica el **Bottom** (Mínimo intrames) como punto ideal de compra. (Línea VERDE)
  - Si el mes es **Bajista** (Cierre < Apertura): Se identifica el **Peak** (Máximo intrames) como punto ideal de venta/corto. (Línea ROJA)

## Interpretación de Resultados

### Significancia Estadística (P-Value)
Es el filtro de calidad más importante.
- **$p < 0.05$ (⭐⭐⭐)**: **Patrón Robusto**. Ej: Septiembre Bajista en S&P 500. Es muy improbable que sea suerte.
- **$p < 0.10$ (⭐⭐)**: **Patrón Moderado**. Ej: Julio Alcista en Nasdaq. Señal fuerte pero con cierta varianza.
- **$p > 0.10$ (⭐)**: **Ruido Probable**. El promedio puede ser alto, pero la volatilidad es tanta que no es confiable (ej. Febrero en Nasdaq).

### Patrones Clave Identificados (Historical)

| Activo | Mes | Tendencia | Hit Rate | P-Value | Insight Operativo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S&P 500** | **Julio** | 🟢 Alcista | **Alto** | **< 0.01** | El "Rey Julio". Históricamente el mes más fuerte y seguro. |
| **S&P 500** | **Septiembre** | 🔴 Bajista | 45% | **< 0.05** | El único mes estructuralmente bajista ("Oso de Septiembre"). |
| **S&P 500** | **Diciembre** | 🟢 Alcista | Alto | **< 0.05** | "Santa Claus Rally". Confirmado estadísticamente. |
| **Nasdaq 100** | **Febrero** | 🔴 Bajista | 38% | > 0.10 | Promedio muy negativo (-1.3%), pero alta volatilidad (cisnes negros). Riesgoso. |
| **Nasdaq 100** | **Noviembre** | 🟢 Alcista | 73% | < 0.10 | Inicio de rally de fin de año. Muy confiable en Tech. |

## Auditoría y Validación
El sistema cuenta con un script de auditoría (`audit_seasonality.py`) que verifica matemáticamente los cálculos usando datos sintéticos controlados, asegurando que:
1. El cálculo de promedios maneja correctamente los retornos logarítmicos/simples.
2. La detección de Peaks/Bottoms es exacta.
3. Los Hit Rates se calculan sobre la muestra correcta.

---
**Nota**: El análisis de estacionalidad debe usarse como un **filtro de sesgo (Bias)**, no como una señal de entrada única. Combínalo siempre con estructura de mercado y acción de precio.
