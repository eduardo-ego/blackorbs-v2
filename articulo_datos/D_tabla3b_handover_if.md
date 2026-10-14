# D1b — Métricas de etapa 2 (Isolation Forest) vs. tamaño de entrenamiento

Se inyecta un escalón fijo de +4 C sobre una lectura normal y se mide si Isolation Forest (entrenado solo con las N lecturas previas) lo marca como anómalo, para distintos N. Justifica el umbral MIN_LECTURAS_MODELO_APRENDIDO=200.

| N entrenamiento | N evaluados | Tasa detección escalón +4°C | Normalidad % media |
|---|---|---|---|
| 100 | 0 | nan% | nan |
| 200 | 25 | 100.00% | 0.6 |
| 500 | 25 | 96.00% | 3.8 |
| 1000 | 25 | 96.00% | 3.8 |
