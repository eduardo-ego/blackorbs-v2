# F3 — Reinicio por Piper (TTS)

**No se encontró evidencia de esto en ningún lado del sistema.**

Búsquedas realizadas sobre el journal completo (persistente desde 2025-04-30):

- `journalctl | grep -i piper` → **0 coincidencias**. Nunca aparece la palabra "Piper" en ningún
  log del sistema.
- `journalctl | grep "/tts"` → 7 coincidencias, pero **no son actividad de un proceso de
  texto-a-voz**: son líneas de `sudo` cuyo `PWD` es literalmente el directorio
  `/home/blackorbs/blackorbs-v2/tts` (comandos `cp`/`systemctl` ejecutados el 2026-08-23 10:56:29,
  al momento de instalar los servicios systemd de blackorbs-v2). Coincide con la cadena `/tts` por
  el nombre del directorio, no por una herramienta Piper.
- No existe ningún directorio, proceso, servicio ni paquete relacionado con "piper" en el sistema
  (no hay `blackorbs-v2-tts.service` ni similar entre los servicios activos).
- Se revisaron también los boot markers (`-- Boot ... --`, `journalctl --list-boots`): ninguno
  ocurre en una ventana de ~21 s después de las líneas `/tts` encontradas arriba (esas líneas no
  están seguidas de un reinicio).

## Conclusión para el artículo

El escenario "reinicio del sistema causado por actividad de Piper ~21 s antes" descrito en las
instrucciones **no corresponde a nada verificable en este dispositivo**. Es posible que: (a) se
refiera a una prueba con un componente de texto-a-voz que nunca se desplegó en este device_id /
esta instalación, (b) se haya confundido con otro proyecto, o (c) sea una prueba planeada pero no
ejecutada todavía. **Se necesita que el autor aclare a qué corresponde este punto** — si hay un
servicio Piper corriendo en otro dispositivo o en una versión distinta del código, hay que apuntar
esta búsqueda a esa fuente en vez de a este journal.
