# D2 — Tabla 4: evaluación rolling-origin del forecast

Horizonte real del sistema: 60 min (HORIZONTE_MINUTOS en ml/config.py). Origen evaluado cada 20 muestras, historial capado a 2000 lecturas (igual que ml/db.py en producción).
'sistema' = ml/forecast.py::generar_forecast (código real, decide persistencia vs. Holt damped según MIN_PUNTOS_HOLT). 'persistencia' = baseline naive pura (siempre último valor observado), evaluada con el mismo horizonte en pasos.
Tiempo de CPU medio de generar_forecast(): 133.80 ms/llamada (1012 llamadas).

| Grupo | Variable | N | MAE sistema | RMSE sistema | MAE persistencia | RMSE persistencia |
|---|---|---|---|---|---|---|
| todos | temperature | 1012 | 1.607 | 3.085 | 1.557 | 2.843 |
| todos | humidity | 1012 | 3.860 | 6.571 | 3.735 | 6.288 |
| confianza_baja | temperature | 6 | 0.860 | 1.309 | 0.860 | 1.309 |
| confianza_baja | humidity | 6 | 1.610 | 2.981 | 1.610 | 2.981 |
| confianza_alta | temperature | 1006 | 1.611 | 3.092 | 1.562 | 2.850 |
| confianza_alta | humidity | 1006 | 3.874 | 6.587 | 3.748 | 6.302 |

Detalle por origen individual: `D_tabla4_detalle_origenes.csv`.
