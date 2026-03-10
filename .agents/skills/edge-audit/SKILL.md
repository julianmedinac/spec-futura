---
name: edge-audit
description: >
  Audita todos los trading edges del sistema SPEC contra los charts de investigación.
  Verifica probabilidades, T-stats, avg_ret en api/index.py contra los PNG de output/.
  Implementa fixes, agrega edges faltantes y hace deploy a Vercel.
---

# Edge Audit Skill — SPEC Research

Usa este skill cuando necesites auditar, corregir o agregar trading edges al dashboard live en specstats.com.

---

## Arquitectura del sistema

```
specstats.com → public/index.html → /api/index (api/index.py)   ← LIVE API
                                                                   ← ÚNICO archivo que importa para el sitio

run_live_monitor.py → src/engine/alpha_brain.py                  ← Monitor local únicamente
                    → src/engine/alpha_constants.py               ← Constantes compartidas (NO sirve la API)
```

> **CRÍTICO:** Cualquier edge agregado solo a `alpha_brain.py` o `alpha_constants.py` NO aparece en specstats.com.
> Todos los cambios deben ir a `api/index.py`.

---

## Tablas de probabilidades en `api/index.py`

| Tabla | Descripción | Fuente Chart |
|-------|-------------|--------------|
| `W2_MONTHLY` | Cierre mensual condicionado al W2 position (12 meses × 4 activos) | `output/charts/strategy/W2/*.png` |
| `WEEKLY_SEASONAL` | D2 fractal: Dividido en Tiers (`bull_75`, `bull_50`, `bear_25`, `bear_50`) | `output/charts/strategy/D2/*_weekly_fractal_seasonality_styled.png` |
| `WEEKLY_ALPHA_MATRIX` | Mean reversion semanal (solo Mean Rev; Momentum eliminado T<1) | `output/charts/Multi/weekly/alpha_matrix_all_indices_weekly.png` |
| `WEEKLY_BIAS_TRIGGERS` | σ breach diario → dirección cierre semanal (7 triggers) | `output/charts/Multi/daily/weekly_bias_inertia_matrix.png` |
| `MONTHLY_BIAS` | Probabilidad histórica de cierre verde por mes | `output/charts/seasonality/{ASSET}/monthly/{ASSET}_monthly_seasonality.png` |
| `DAILY_ALPHA_TRIGGERS` | σ breach ayer → dirección D+1 (3 edges tradeables) | `output/charts/Multi/daily/daily_alpha_matrix_weekdays.png` |
| `SIGMA_UPPER/LOWER` | Umbrales asimétricos DOR (drive/panic) por activo | `output/charts/*/daily/DOR_O2C_D_*_2020-2025_*.png` |

---

## Protocolo de auditoría

### Paso 1 — Leer los charts
Siempre ver los PNG con `view_file` antes de tocar el código:

```python
# Charts clave en orden de importancia:
output/charts/Multi/daily/weekly_bias_inertia_matrix.png      # WEEKLY_BIAS_TRIGGERS
output/charts/Multi/daily/daily_alpha_matrix_weekdays.png     # DAILY_ALPHA_TRIGGERS
output/charts/strategy/W2/{NQ,ES,YM,GOLD}.png                 # W2_MONTHLY
output/charts/strategy/D2/{NQ,ES}_weekly_fractal_seasonality_styled.png  # WEEKLY_SEASONAL
output/charts/seasonality/{ASSET}/monthly/{ASSET}_monthly_seasonality.png # MONTHLY_BIAS
```

### Paso 2 — Cross-reference con el código
Comparar cada valor en el chart contra su constante en `api/index.py`.
Campos a verificar por trigger: `prob`, `avg_ret`, `t_stat`, `grade`.

**Regla de grading:**
- `DIAMOND`: prob ≥ 90%
- `GOLD+`: prob ≥ 82%
- `GOLD`: prob ≥ 75%
- `SILVER`: prob < 75%

**Para D+1 edges, filtrar por T-stat:**
- Incluir: T ≥ 1.3
- Excluir (NOISE): T < 0.5

### Paso 3 — Aplicar fixes
Editar solo `api/index.py`. Verificar sintaxis después:

```powershell
py -c "import ast; ast.parse(open('api/index.py', encoding='utf-8').read()); print('SYNTAX OK')"
```

### Paso 4 — Deploy
```powershell
vercel --prod
```

---

## Valores auditados (2026-03-04)

### `WEEKLY_BIAS_TRIGGERS` — Valores correctos del chart

```python
WEEKLY_BIAS_TRIGGERS = {
    ('NQ', 0, 'drive'):  {'direction': 'BULL', 'prob': 82.3, 'avg_ret': '+2.82%', 't_stat': 6.53, 'grade': 'GOLD+'},
    ('NQ', 4, 'panic'):  {'direction': 'BEAR', 'prob': 84.5, 'avg_ret': '-2.44%', 't_stat': 7.40, 'grade': 'GOLD+'},
    ('ES', 0, 'drive'):  {'direction': 'BULL', 'prob': 86.5, 'avg_ret': '+2.65%', 't_stat': 7.30, 'grade': 'GOLD+'},
    ('ES', 4, 'panic'):  {'direction': 'BEAR', 'prob': 91.8, 'avg_ret': '-2.16%', 't_stat': 5.97, 'grade': 'GOLD+'},
    ('NQ', 3, 'panic'):  {'direction': 'BEAR', 'prob': 78.5, 'avg_ret': '-2.12%', 't_stat': 6.26, 'grade': 'GOLD'},
    ('YM', 2, 'panic'):  {'direction': 'BEAR', 'prob': 75.5, 'avg_ret': '-1.93%', 't_stat': 4.58, 'grade': 'GOLD'},
    ('ES', 1, 'drive'):  {'direction': 'BULL', 'prob': 75.5, 'avg_ret': '+1.75%', 't_stat': 3.65, 'grade': 'SILVER'},
    # NQ/ES Wed Drive omitido — D2 ya establece el sesgo semanal antes del miércoles
}
```

### `DAILY_ALPHA_TRIGGERS` — D+1 edges tradeables

```python
DAILY_ALPHA_TRIGGERS = {
    ('NQ', 1, 'panic'):  {'signal': 'REBOUND (Miércoles)', 'prob': 55.4, 'avg_ret_d1': '+0.543%', 't_stat': 2.1,  'grade': 'GOLD (T>2.1)'},
    ('YM', 4, 'panic'):  {'signal': 'REBOUND (Lunes)',     'prob': 67.9, 'avg_ret_d1': '+0.444%', 't_stat': 1.5,  'grade': 'SILVER (T>1.5)'},
    ('NQ', 3, 'drive'):  {'signal': 'REVERSION (Viernes)', 'prob': 57.8, 'avg_ret_d1': '-0.271%', 't_stat': 1.4,  'grade': 'BRONZE (T>1.3)'},
}
```

---

## Lógica de la capa diaria (D+1)

```python
# CORRECTO: checa la barra ANTERIOR (df.iloc[-2]) para que el signal
# aparezca el día de la predicción (D+1), NO el día del trigger.
prev_bar = df.iloc[-2]
prev_weekday = prev_bar.name.weekday()  # 0=Mon … 4=Fri
prev_o2c = (prev_bar['Close'] - prev_bar['Open']) / prev_bar['Open']

if prev_o2c > SIGMA_UPPER[asset]:
    trigger = DAILY_ALPHA_TRIGGERS.get((asset, prev_weekday, 'drive'))
elif prev_o2c < SIGMA_LOWER[asset]:
    trigger = DAILY_ALPHA_TRIGGERS.get((asset, prev_weekday, 'panic'))
```

**Ejemplo:**
- Martes NQ cierra < -1.486% → miércoles aparece "REBOUND (Miércoles) 55.4%"
- Jueves NQ cierra > +1.634% → viernes aparece "REVERSION (Viernes) 57.8%"

---

## Reglas de diseño

1. **Wednesday Drive NO va en WEEKLY_BIAS_TRIGGERS** — D2 ya establece el sesgo semanal desde el martes. Agregarla crea redundancia confusa para el usuario.
2. **Bull Momentum eliminado de WEEKLY_ALPHA_MATRIX** — T < 1, no significativo. Solo Mean Reversion permanece.
3. **Sigma asimétrico** — `api/index.py` usa `SIGMA_UPPER/LOWER` distintos (DOR-calculado). `alpha_brain.py` usa sigma simétrico (menos preciso). La API es la fuente de verdad.
4. **D+1 NOISE excluido** — Fri NQ Continuation (T<0.5) y Wed YM Rebound (T<0.4) excluidos explícitamente.

---

## Checklist de verificación antes de deploy

```
[ ] py -c "import ast; ast.parse(open('api/index.py').read()); print('OK')"
[ ] Buscar valores viejos con grep para confirmar que fueron reemplazados
[ ] Confirmar que daily layer usa df.iloc[-2] (prev bar), no df.iloc[-1]
[ ] vercel --prod → esperar "Aliased: https://specstats.com"
[ ] Abrir browser en specstats.com y verificar visualmente
```

---

## Discrepancias típicas a buscar

Si los valores en el código son **1-4% más altos** que el chart, probablemente se entraron de un run con parámetros diferentes al auditado. Siempre usar el chart como fuente de verdad, no el `alpha_brain.py`.

| Síntoma | Causa probable |
|---------|----------------|
| Probs infladas 1-4% vs chart | Código editado desde run anterior diferente al auditado |
| Edge aparece en `alpha_brain.py` pero no en site | Solo en monitor local, nunca llegó a `api/index.py` |
| Columna DIARIO siempre vacía | `daily: {'signals': []}` hardcodeado o usando `df.iloc[-1]` |
| Signal aparece el día equivocado | D+1 trigger chequeando barra actual en lugar de la anterior |
