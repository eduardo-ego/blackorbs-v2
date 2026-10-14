# G — Verificaciones bibliográficas y evidencia socio-técnica (para el autor)

Estas tres verificaciones, tal como dice la instrucción original, **no viven en el dispositivo**:
no hay artículos citados, `.bib`, ni notas de campo en `/home/blackorbs` (se buscó explícitamente —
no existe ningún PDF, `.bib`, ni archivo con "articulo"/"tesis" en el nombre en todo el home). No
hay nada que yo pueda extraer aquí; quedan como pendientes explícitos para ti:

## G1 — Celdas "Partial" de la Tabla 1

Necesitas los PDFs/textos de: Hassan (2020), Medagedara (2024), Roostaei (2023), Halenár (2025),
Dera (2026), Hidalgo-Castelo (2026) para confirmar contra qué se comparó cada celda "Partial". Si
me compartes esos textos (o las secciones relevantes) en una próxima sesión, puedo ayudarte a
cotejarlos contra las afirmaciones de la Tabla 1.

## G2 — Cita "priorización de eventos (Zhang et al., 2021)"

Confirmar si la referencia correcta en la bibliografía del v16 es "Zhang y Tao (2021)" (dos
autores, no "et al."). Esto es una revisión de tu propio archivo de bibliografía del artículo v16,
que tampoco está en este dispositivo — reviéndalo directamente en el documento del artículo.

## G3 — Evidencia socio-técnica de planta (sección 5.1)

Número de alertas atendidas, tiempo de reacción antes/después, comentarios del personal: esto es
información operativa/humana que no se registra en ningún log ni base de datos del sistema (el
sistema solo guarda si se *generó* una alerta y su mensaje — no si alguien la atendió, cuánto
tardó, ni qué opinó). Tendrías que recolectarla por separado (entrevistas, bitácora de planta,
etc.). Como referencia cuantitativa parcial, `data/blackorbs.db` sí tiene:
- 2808 alertas tipo "ML" generadas automáticamente (ver `E_consultas_ia.csv` para contexto de uso
  del chat, y la tabla `alertas` completa si la quieres exportar aparte con una consulta como la de
  `E_consultas_ia`, cambiando `consultas_ia` por `alertas`).
- Ninguna columna de "atendida"/"resuelta" más allá de `status='Active'` fijo en todas las filas
  (columna `status` no se actualiza en ningún lado del código — otro hallazgo a documentar: el
  campo existe en el esquema pero el backend nunca lo cambia de 'Active').
