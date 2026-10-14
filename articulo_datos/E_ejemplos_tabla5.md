# E_ejemplos_tabla5 — Una interacción real por intención

## estado_actual

**Pregunta:** ¿Cómo está el ambiente ahorita?
**Proveedor:** claude  
**Latencia:** 7.90 s

**Respuesta:**
```
El ambiente está en **modo atención** 🟡

**Última lectura (06/09, 08:35 p.m.):**
- Temperatura: 25.51 °C
- Humedad: 55.28 %

**Qué detectó el sistema:** el modelo marca esta combinación de lecturas como inusual, con la humedad como probable causa (normalidad del 10%).

**Pronóstico para la próxima hora** (confianza alta): 26.4 °C y 52.44 % de humedad, o sea que la humedad tendería a bajar un poco.

¿Quieres que revise la tendencia de los últimos minutos o las alertas recientes?
```

## estadisticas_periodo

**Pregunta:** ¿Cuál fue la temperatura promedio en la última hora?
**Proveedor:** claude  
**Latencia:** 14.33 s

**Respuesta:**
```
No pude obtener una respuesta clara, intenta reformular la pregunta.
```

## comparacion_periodos

**Pregunta:** ¿La temperatura de la última hora es más alta que la de las dos horas anteriores?
**Proveedor:** claude  
**Latencia:** 14.62 s

**Respuesta:**
```
No pude obtener una respuesta clara, intenta reformular la pregunta.
```

## recuerdo_alertas

**Pregunta:** ¿Cuáles son las alertas más recientes?
**Proveedor:** claude  
**Latencia:** 6.52 s

**Respuesta:**
```
Estas son las 10 alertas más recientes (todas activas y generadas por el modelo de ML):

**Últimas alertas — 06/09**
- **08:40 p.m.** – Atención: lectura inusual (temperatura)
- **08:20 p.m.** – Atención: lectura inusual (humedad)
- **08:18 p.m.** – Atención: lectura inusual (temperatura)
- **08:16 p.m.** – Atención: lectura inusual (temperatura)
- **08:10 p.m.** – Atención: el forecast anticipa que las condiciones podrían salirse de rango pronto
- **07:53 p.m.** – Atención: lectura inusual (temperatura)
- **07:46 p.m.** – Atención: lectura inusual (temperatura)
- **07:44 p.m.** – 🔴 Crítico: lectura inusual (temperatura)
- **07:43 p.m.** – Atención: lectura inusual (temperatura)
- **07:40 p.m.** – 🔴 Crítico: lectura inusual (temperatura)

**Resumen:** la mayoría apunta a la temperatura como causa probable, con dos alertas críticas alrededor de las 07:40–07:44 p.m. ¿Quieres que revise el estado actual o la tendencia de las últimas lecturas?
```

## fuera_de_alcance

**Pregunta:** ¿Cuál es el pronóstico del clima para mañana en la ciudad?
**Proveedor:** claude  
**Latencia:** 8.03 s

**Respuesta:**
```
Una aclaración importante: yo no tengo acceso a pronósticos meteorológicos de la ciudad. Solo puedo darte lo que mide y proyecta este dispositivo en su ubicación, y su horizonte es de corto plazo (1 hora), no de mañana.

Esto es lo que hay calculado ahora mismo (08:43 p.m.):

- **Estado:** contento — patrón conjunto de temperatura/humedad dentro de lo normal.
- **Pronóstico a 60 minutos:** 23.55 °C y 61.33 % de humedad, con confianza alta.

Si quieres, puedo mostrarte la tendencia de las últimas horas o las alertas recientes del sensor. Para el clima de mañana en la ciudad necesitarías un servicio meteorológico externo.
```

