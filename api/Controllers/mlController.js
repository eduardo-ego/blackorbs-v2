import db from '../db/index.js';
import { notificarAnomalia } from '../Services/alertNotifier.js';

const MOODS = new Set(['happy', 'attention', 'critical', 'thinking']);
const MOODS_QUE_ALERTAN = new Set(['attention', 'critical']);

const upsertEstado = db.prepare(`
  INSERT INTO ml_estado (device_id, mood, anomaly_score, anomaly_variable, normalidad_pct, forecast_temperature, forecast_humidity, forecast_horizon_minutes, forecast_confianza, message, updated_at)
  VALUES (@device_id, @mood, @anomaly_score, @anomaly_variable, @normalidad_pct, @forecast_temperature, @forecast_humidity, @forecast_horizon_minutes, @forecast_confianza, @message, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
  ON CONFLICT(device_id) DO UPDATE SET
    mood = excluded.mood,
    anomaly_score = excluded.anomaly_score,
    anomaly_variable = excluded.anomaly_variable,
    normalidad_pct = excluded.normalidad_pct,
    forecast_temperature = excluded.forecast_temperature,
    forecast_humidity = excluded.forecast_humidity,
    forecast_horizon_minutes = excluded.forecast_horizon_minutes,
    forecast_confianza = excluded.forecast_confianza,
    message = excluded.message,
    updated_at = excluded.updated_at
`);

const selectEstado = db.prepare('SELECT * FROM ml_estado WHERE device_id = ?');

// Llamado por el servicio Python de ML (anomaly.py / forecast.py), nunca por el LLM directamente.
export const updateMlState = async (req, res) => {
  const {
    mood,
    anomaly_score = null,
    anomaly_variable = null,
    normalidad_pct = null,
    forecast_temperature = null,
    forecast_humidity = null,
    forecast_horizon_minutes = null,
    forecast_confianza = null,
    message = null,
  } = req.body;

  const deviceId = req.app.get('deviceId');

  if (!MOODS.has(mood)) {
    return res.status(400).json({ error: `invalid mood, must be one of ${[...MOODS].join(', ')}` });
  }

  try {
    const estadoAnterior = selectEstado.get(deviceId);

    upsertEstado.run({
      device_id: deviceId,
      mood,
      anomaly_score,
      anomaly_variable,
      normalidad_pct,
      forecast_temperature,
      forecast_humidity,
      forecast_horizon_minutes,
      forecast_confianza,
      message,
    });

    const estado = selectEstado.get(deviceId);

    const io = req.app.get('io');
    if (io) io.emit('mlUpdate', estado);

    // Solo notifica en la transición hacia un mood peor, no en cada ciclo del ML mientras se mantiene igual.
    if (MOODS_QUE_ALERTAN.has(mood) && mood !== estadoAnterior?.mood) {
      notificarAnomalia({
        deviceId,
        mood,
        anomalyVariable: anomaly_variable,
        anomalyScore: anomaly_score,
        message,
      }).catch((err) => console.error('❌ Error notifying anomaly:', err));
    }

    res.json(estado);
  } catch (err) {
    console.error('❌ Error in updateMlState:', err);
    res.status(500).json({ error: 'Error saving ML state' });
  }
};

export const getMlState = async (req, res) => {
  try {
    const deviceId = req.app.get('deviceId');
    const estado = selectEstado.get(deviceId);
    res.json(estado || { device_id: deviceId, mood: 'happy', message: 'No ML data yet' });
  } catch (err) {
    console.error('❌ Error in getMlState:', err);
    res.status(500).json({ error: 'Error fetching ML state' });
  }
};
