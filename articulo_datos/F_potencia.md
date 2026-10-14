# F5 — Medición de potencia con el servicio ML activo (plantilla)

No es medible desde software (el consumo eléctrico real requiere instrumentación externa). Esta es
una plantilla de procedimiento para que el autor la ejecute con un medidor USB/DC físico.

## Material necesario

- Medidor de potencia USB-C o DC en línea (p. ej. USB power meter con lectura de V/A/W, o un
  medidor DC si la CM5 se alimenta por pines).
- El dispositivo con **todos los servicios corriendo**: `blackorbs-v2-api`,
  `blackorbs-v2-sensor`, `blackorbs-v2-ml`, `blackorbs-v2-display` (confirmar con
  `systemctl status blackorbs-v2-*` antes de empezar — al momento de esta extracción los 4 estaban
  `active running`).

## Procedimiento sugerido

1. Conectar el medidor entre la fuente de alimentación y la CM5.
2. Dejar correr 5 minutos de estabilización antes de empezar a registrar (para que el primer ciclo
   de Isolation Forest ya haya ocurrido y no se mida un pico de arranque atípico).
3. Registrar **V, A, W** cada 10–30 s durante **1 hora continua**, idealmente con un medidor que
   permita exportar el log (si es manual, anotar en una hoja con columnas: `hora, V, A, W`).
4. Anotar también, durante esa misma hora, los momentos en que el servicio ML corre su ciclo
   (`CICLO_SEGUNDOS = 60 s`, ver `A_parametros_ml.md`) vs. cuando está dormido, para poder
   correlacionar picos de consumo con el reentrenamiento de Isolation Forest (que ocurre en
   *cada* ciclo, ver hallazgo en `A_parametros_ml.md`).
5. Calcular: potencia media (W), potencia máxima (W), y energía total consumida en la hora (Wh).
6. Repetir opcionalmente con `blackorbs-v2-ml` detenido (`sudo systemctl stop blackorbs-v2-ml`)
   para poder reportar el delta de consumo atribuible específicamente al servicio de ML — esto
   sería el dato más útil para la sección 4.6, ya que aísla el costo energético del pipeline de
   ML del resto del sistema (sensor + display + api). **Recuerda reiniciar el servicio
   (`sudo systemctl start blackorbs-v2-ml`) al terminar la prueba.**

## Tabla a llenar

| Configuración | V media | A media | W medio | W máximo | Energía en 1h (Wh) |
|---|---|---|---|---|---|
| Todos los servicios activos | | | | | |
| Sin `blackorbs-v2-ml` (opcional, para aislar el costo del ML) | | | | | |

## Referencia de apoyo (medido en este documento)

- `D_recursos_ml.md` da CPU%/RAM del proceso ML (medido con `psutil`, no potencia) y el tiempo de
  entrenamiento de Isolation Forest — útil para correlacionar con los picos de W que se midan aquí.
