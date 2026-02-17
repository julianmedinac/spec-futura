# SPEC RESEARCH - DOR Framework

## Estructura del Proyecto

### 🚀 Aplicación y Dashboard (`/dashboard_app`)
Contiene todo lo necesario para el funcionamiento del sitio web y el monitor en vivo.
- `api/`: Backend serverless (Python) para Vercel.
- `public/`: Archivos estáticos del Dashboard Alpha.
- `live_dashboard.html`: Interfaz del Monitor en Vivo "SPEC FUTURA".
- `run_live_monitor.py`: Script que alimenta los datos en tiempo real.
- `data/`: Datos de estado de la aplicación.
- `vercel.json` & `requirements.txt`: Configuración de despliegue.

### 🔬 Investigación y Auditoría (`/research_scripts`)
Archivos de análisis histórico, scripts de auditoría y generación de matrices de probabilidad.
- `analyze_*.py`: Scripts de análisis por activo/temporada.
- `audit_*.py`: Scripts para validar datos auditados.
- Matrices de probabilidad y estadísticas históricas.

### 📦 Núcleo del Sistema (`/src` & `/config`)
El motor de cálculo (`engines`), cargadores de datos (`data`) y configuraciones globales compartidas.

### 📂 Otros
- `/docs`: Guías de estilo, estadísticas de W2 y documentación técnica.
- `/output`: Resultados de los scripts de investigación (gráficos, reportes).
