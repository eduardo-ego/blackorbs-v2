# D4 — Consumo de recursos del servicio ML (proceso real, PID 646)

Medido con `psutil` sobre el proceso ya corriendo bajo systemd (`blackorbs-v2-ml`, sin
reiniciarlo), muestreando cada 2 s durante 600 s
(~10 ciclos de 60 s). 300 muestras tomadas.

| Métrica | Media | Máximo |
|---|---|---|
| CPU (%) | 2.32 | 77.50 |
| RSS (MB) | 176.0 | 178.2 |

(CPU % es relativo a un núcleo, como lo reporta `psutil.Process.cpu_percent`; en un ciclo
de 60s el proceso está dormido la mayor parte del tiempo entre ejecuciones de
`ejecutar_ciclo()`, así que el promedio incluye tiempo ocioso.)

## Tiempo de entrenamiento de Isolation Forest (código real, dataset actual)

- Tamaño del dataset de entrenamiento: 2000 lecturas (temperature+humidity sin NaN,
  hasta el límite de 2000 que usa `ml/db.py::cargar_lecturas` en producción).
- 5 repeticiones de `IsolationForest(n_estimators=200, contamination='auto',
  random_state=42).fit(...)`: 293.1 ms, 281.6 ms, 301.0 ms, 277.7 ms, 282.8 ms
- Media: 287.2 ms, máximo: 301.0 ms.

Muestras crudas de CPU/RAM: `D_recursos_ml_muestras.csv`.
