import db from '../db/index.js';
import bot from './telegramService.js';
import sendTeamsAlert from './teamsService.js';

const insertAlerta = db.prepare(`
  INSERT INTO alertas (device_id, type, value, threshold, unit, location, severity, status, message)
  VALUES (@device_id, @type, @value, @threshold, @unit, @location, @severity, @status, @message)
`);

const SEVERIDAD_LEGIBLE = { attention: 'Attention', critical: 'Critical' };
const EMOJI_POR_MOOD = { attention: '🟡', critical: '🔴' };

// Called when the ML state (mlController) transitions to attention/critical.
// Notifies via Telegram and Teams, and logs a record in the `alertas` table.
export async function notificarAnomalia({ deviceId, mood, anomalyVariable, anomalyScore, message }) {
  const severidad = SEVERIDAD_LEGIBLE[mood] || mood;
  const titulo = `${EMOJI_POR_MOOD[mood] || '⚠️'} Blackorbs — ${severidad}`;
  const cuerpo = message || `Anomaly detected in ${anomalyVariable || 'a variable'} (score ${anomalyScore ?? 'N/A'})`;

  insertAlerta.run({
    device_id: deviceId,
    type: 'ML',
    value: anomalyScore,
    threshold: null,
    unit: anomalyVariable,
    location: null,
    severity: severidad,
    status: 'Active',
    message: cuerpo,
  });

  const tareas = [];

  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (chatId) {
    const textoTelegram = `${titulo}\nDevice: ${deviceId}\n${cuerpo}`;
    tareas.push(
      bot.sendMessage(chatId, textoTelegram).catch((err) => {
        console.error('❌ Error sending Telegram alert:', err.message);
      })
    );
  } else {
    console.warn('⚠️ TELEGRAM_CHAT_ID not configured, skipping Telegram alert');
  }

  tareas.push(sendTeamsAlert({ titulo, mensaje: `${cuerpo}\n\nDevice: ${deviceId}`, mood }));

  await Promise.allSettled(tareas);
}
