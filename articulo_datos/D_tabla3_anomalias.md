# D1 — Tabla 3: evaluación del detector de anomalías (offline, sintético)

Semilla fija: 42. 30 inyecciones por familia (escalón, rampa, pico) = 90 inyecciones totales.

Baseline A ('fijo'): temperatura >= 35 C (umbral codificado en api/Controllers/alertController.js); humedad: +-2 sigma del dataset completo (no hay umbral de humedad configurado en el backend).
Baseline B ('zscore_rodante'): |z| >= 2.0 sobre ventana rodante de 60 muestras.
'etapa1' y 'etapa2' llaman directamente a ml/anomaly.py::_detectar_ewma y _detectar_isolation_forest (código real, no reimplementado).

| Detector | Familia | Precisión | Recall | F1 | Retardo medio (muestras) | N | CPU/ciclo (ms) |
|---|---|---|---|---|---|---|---|
| etapa1 | escalon | 0.823 | 0.567 | 0.661 | 0.4 | 30 | 0.44 |
| etapa1 | pico | 0.548 | 0.967 | 0.633 | 0.0 | 30 | 0.44 |
| etapa1 | rampa | 0.885 | 0.789 | 0.814 | 1.5 | 30 | 0.44 |
| etapa2 | escalon | 0.870 | 1.000 | 0.922 | 0.0 | 30 | 280.70 |
| etapa2 | pico | 0.454 | 1.000 | 0.547 | 0.0 | 30 | 280.70 |
| etapa2 | rampa | 0.892 | 0.879 | 0.878 | 3.0 | 30 | 280.70 |
| fijo | escalon | 1.000 | 0.015 | 0.621 | 0.0 | 30 | 0.00 |
| fijo | pico | nan | 0.000 | nan | nan | 30 | 0.00 |
| fijo | rampa | 1.000 | 0.057 | 0.432 | 28.7 | 30 | 0.00 |
| zscore_rodante | escalon | 0.844 | 0.645 | 0.722 | 0.4 | 30 | 0.00 |
| zscore_rodante | pico | 0.532 | 0.944 | 0.598 | 0.1 | 30 | 0.00 |
| zscore_rodante | rampa | 0.902 | 0.837 | 0.848 | 1.4 | 30 | 0.00 |

Detalle por inyección individual: `D_tabla3_detalle_injecciones.csv`.
