# F4 — Latencia de alertas (estado de credenciales)

## Estado de credenciales en `api/.env` (solo se verificó presencia/longitud, nunca el valor)

| Canal | Variables requeridas | Estado |
|---|---|---|
| WhatsApp (Twilio) | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | Las 3 configuradas (no vacías) |
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Las 2 configuradas (no vacías) |
| Microsoft Teams | `TEAMS_WEBHOOK_URL` | **Vacía** — `teamsService.js` detecta esto y omite el envío con un `console.warn`, devolviendo `false` sin lanzar error |
| Email | `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO` | Las 3 configuradas (no vacías) |

Que una variable esté "configurada" solo significa que no está vacía — no confirma que la
credencial sea válida (eso solo se sabe intentando un envío real).

## Envío de prueba real — pendiente de tu confirmación

Falta la parte de "probar un envío" y "medir sobre ≥20 eventos el tiempo desde el timestamp de la
lectura hasta la entrega por canal". Esto implica **enviar mensajes reales** a un número de
WhatsApp/Telegram/email reales (los configurados en `.env`) — no es una operación de solo lectura,
por eso no lo disparé automáticamente. Si quieres que lo haga:

1. Un envío de prueba por canal (confirma si las credenciales son válidas) — usa
   `api/Controllers/alertController.js` (`POST /alert/whatsapp`, `/alert/telegram`,
   `/alert/email`, revisar `api/Routes/alertsRoutes.js` para las rutas exactas) o
   `api/Services/emailService.js`/`telegramService.js`/`whatsappService.js` directamente.
2. Para medir latencia sobre ≥20 eventos reales de punta a punta, la forma más fiel es esperar a
   que el propio sistema genere 20 alertas orgánicas (`mood` transicionando a atencion/critico, ver
   `alertNotifier.js`) y comparar `alertas.timestamp` contra la hora de recepción real en cada
   canal (que hay que registrar manualmente al recibir cada notificación, no queda timestamp de
   "entregado" en ningún lado del código). Dado el volumen actual (2808 alertas históricas, ver
   `E_consultas_ia.csv`/DB), es probable que ya se acumulen ≥20 transiciones nuevas en poco tiempo
   sin necesidad de forzar nada.

**Dime si quieres que dispare los envíos de prueba ahora** (consumen tu crédito de Twilio si
aplica, y llegan de verdad a tu WhatsApp/Telegram/correo configurados) — si prefieres, puedo dejar
solo un script (`F_medir_latencia_alertas.py`) que tú corras cuando quieras, escuchando
`alertas` nuevas y pidiéndote confirmar manualmente la hora de llegada por canal.
