import db from '../db/index.js';
import sendAlert from '../Services/whatsappService.js';
import sendAlertEmail from '../Services/emailService.js';
import bot from '../Services/telegramService.js';

const insertAlerta = db.prepare(`
  INSERT INTO alertas (device_id, type, value, threshold, unit, location, severity, status, message)
  VALUES (@device_id, @type, @value, @threshold, @unit, @location, @severity, @status, @message)
`);

const selectAlertas = db.prepare(`SELECT * FROM alertas ORDER BY timestamp DESC LIMIT ?`);

function determineSeverity(value) {
  if (value >= 50) return 'Critical';
  if (value >= 40) return 'High';
  if (value >= 30) return 'Medium';
  return 'Low';
}

function guardarAlerta({ deviceId, temperature, sensor }) {
  insertAlerta.run({
    device_id: deviceId || null,
    type: 'Temperature',
    value: temperature,
    threshold: 35,
    unit: '°C',
    location: sensor || 'Unknown',
    severity: determineSeverity(temperature),
    status: 'Active',
    message: `High temperature detected: ${temperature}°C at sensor ${sensor}`,
  });
}

export const sendAlertWhats = async (req, res) => {
  const { temperature, humidity, sensor } = req.body;
  try {
    await sendAlert(process.env.ALERT_WHATSAPP_TO, temperature, humidity, sensor);
    guardarAlerta({ deviceId: req.app.get('deviceId'), temperature, sensor });
    res.json('Alert sent and saved');
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error sending or saving the alert' });
  }
};

export const sendAlertTelegram = async (req, res) => {
  const { temperature, humidity, sensor } = req.body;
  try {
    const telegramChatId = process.env.TELEGRAM_CHAT_ID;
    const message = `⚠️ Alert\nSensor: ${sensor}\nTemperature: ${temperature}°C\nHumidity: ${humidity}%`;
    await bot.sendMessage(telegramChatId, message);
    guardarAlerta({ deviceId: req.app.get('deviceId'), temperature, sensor });
    res.json('Telegram alert sent and saved');
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error sending or saving the Telegram alert' });
  }
};

export const sendAlertEmailController = async (req, res) => {
  const { temperature, humidity, sensor } = req.body;

  if (!temperature || !humidity || !sensor) {
    return res.status(400).json({ error: 'Missing fields: temperature, humidity or sensor' });
  }

  try {
    const tempSent = await sendAlertEmail(sensor, 'Temperature', temperature);
    const humSent = await sendAlertEmail(sensor, 'Humidity', humidity);
    const success = tempSent && humSent;

    if (success) {
      res.status(200).json({ message: 'Alerts sent by email' });
    } else {
      res.status(500).json({ error: 'Could not send one or both alerts' });
    }
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

export const getAlerts = async (req, res) => {
  try {
    const limit = Number(req.query.limit) || 200;
    res.json(selectAlertas.all(limit));
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error fetching alerts' });
  }
};
