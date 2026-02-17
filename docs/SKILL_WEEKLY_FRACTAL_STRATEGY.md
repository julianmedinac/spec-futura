---
name: Weekly Fractal Strategy (D1-D2)
description: Estrategia de trading cuantitativa basada en la relación fractal de los primeros dos días de la semana (D1-D2). Explota la inercia semanal y patrones estacionales de alta probabilidad (>80% Win Rate).
---

# Weekly Fractal Strategy (D1-D2)

## 🎯 Concepto Central

La estrategia se basa en una premisa estadística simple pero poderosa:
**"Como cierra el Martes (D2) en relación al rango Lunes-Martes (D1-D2) predice el resto de la semana."**

*   **Señal**: Cierre del Martes vs el 50% del Rango D1-D2.
*   **Confirmación**: Ruptura del Rango el Miércoles (D3).
*   **Ejecución**: Capturar la expansión de rango el Jueves/Viernes (Extension).

---

## 🚦 Reglas de la Estrategia

### 1. La Señal (Martes / D2 Close)
Calcula el rango total de Lunes y Martes (`High_D1_D2 - Low_D1_D2`).
Calcula el punto medio (50%).

*   **BULL SIGNAL 🟢**: Si el Martes cierra **POR ENCIMA** del 50%.
*   **BEAR SIGNAL 🔴**: Si el Martes cierra **POR DEBAJO** del 50%.

### 2. La Confirmación (Miércoles / D3 Breakout)
Solo operamos si el precio "confirma" la intención rompiendo el rango.

*   **Para Bull**: Esperar que el precio rompa el **Máximo de D1-D2**.
*   **Para Bear**: Esperar que el precio rompa el **Mínimo de D1-D2**.

### 3. La Salida (Thu/Fri Extension vs Hold)
Aquí es donde la estadística (Seasonality) es crítica.
*   **Estándar**: Vender en la **Extensión** (Nuevo Máximo/Mínimo el Jueves/Viernes).
*   **Hold**: Solo mantener al cierre semanal en meses específicos (ej. Noviembre).

---

## 📊 Estadísticas de Alto Nivel

### Win Rates Generales (Todos los Meses)
| Activo | Señal | Evento (Probabilidad) | Win Rate |
| :--- | :--- | :--- | :--- |
| **NQ** | Bull | Nuevo Máximo Semanal | **80.0%** |
| **ES** | Bull | Nuevo Máximo Semanal | **82.4%** |
| **DJI** | Bull | Nuevo Máximo Semanal | **77.6%** |
| **GC** | Bull | Nuevo Máximo Semanal | **75.5%** |

---

## 🗓️ Sniper Setups (Estrategias Estacionales >85%)

Estos son los meses donde la estrategia es **CASI INFALIBLE**. Aumentar tamaño de posición.

### 🟢 THE JANUARY EFFECT (Enero)
*   **Activos**: NQ, ES, GC.
*   **Señal**: Bull (Martes > 50%).
*   **Win Rate**: **86-88%**.
*   **Táctica**: Compra agresiva en rupturas.

### 🟢 THE JUNE BREAKOUT (Junio)
*   **Activos**: NQ, GC.
*   **Señal**: **BIDIRECCIONAL**. Funciona igual de bien para **Largos** (85%) y **Cortos** (82%).
*   **Táctica**: El mes de la volatilidad. Sigue la dirección de la ruptura del Miércoles sin dudar.

### 🟢 APRIL BULL (Abril)
*   **Activos**: NQ.
*   **Señal**: Bull.
*   **Win Rate**: **85.0%**.

### 🟢 NOVEMBER RUNNER (Noviembre)
*   **Activos**: Todos (Indices).
*   **Señal**: Bull.
*   **Característica Especial**: Es el mejor mes para hacer **HOLD** hasta el Viernes (Probabilidad de cerrar en máximos > 65%).

---

## ⚠️ Zonas de Peligro (Trampas Estadísticas)

### 🔴 FEBRERO (La Trampa del Cierre)
*   **Patrón**: El mercado da señal Bull, rompe máximos el Miércoles/Jueves... y se devuelve.
*   **Probabilidad de Extensión**: ALTA (>75%).
*   **Probabilidad de Hold Gains**: **MUY BAJA (<50%)**.
*   **Acción**: **TAKE PROFIT AGRESIVO**. Vende la ruptura, NO aguantes hasta el cierre del Viernes.

### 🔴 DICIEMBRE (Ruido)
*   **Patrón**: Win Rates más bajos (~68-74%). Mucho ruido por bajo volumen.
*   **Acción**: Reducir tamaño o no operar fractal semanal.

---

## 📉 Gestión de la Operación (Trade Management)

### Escenario Post-Breakout (Miércoles ya rompió)
Si ya entraste y el mercado marcó nuevo máximo:

1.  **Probabilidad de Continuación (Jue/Vie)**: **~70%**.
    *   Mantén la posición buscando un nuevo impulso.
2.  **Probabilidad de Cerrar Verde**: **~80%**.
    *   Tu Stop Loss (Breakeven) está muy seguro.
3.  **Probabilidad de Cerrar MEJOR que el Miércoles**: **~55% (Moneda al aire)**.
    *   **REGLA DE ORO**: Si el Jueves/Viernes hace un nuevo máximo (spike), **VENDE**. No esperes al cierre semanal. La estadística dice que el precio probablemente retroceda.

---

## 🛠️ Herramientas del Sistema

Ubicación de scripts clave para análisis en tiempo real:

1.  **Auditoría en Tiempo Real**:
    ```bash
    py check_nq_w2_status.py
    ```
    *Te dice si la semana actual (y el mes) están en configuración Bull/Bear.*

2.  **Tablas de Probabilidad (Estilo Matrix)**:
    ```bash
    py export_weekly_fractal_table_styled.py
    ```
    *Genera las tablas de calor Negro/Verde para NQ, ES, DJI, GC.*

3.  **Análisis de Continuación (Exit Strategy)**:
    ```bash
    py visualize_weekly_continuation_seasonal.py
    ```
    *Genera las tablas de decisión "Hold vs Sell" por mes.*
