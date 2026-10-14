import db from '../db/index.js';

const insertLectura = db.prepare(`
  INSERT INTO lecturas (device_id, temperature, humidity, pressure)
  VALUES (@device_id, @temperature, @humidity, @pressure)
`);

const selectLecturas = db.prepare(`
  SELECT * FROM lecturas WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?
`);

export const postData = async (req, res) => {
  const { temperature, humidity, pressure = null } = req.body;
  const deviceId = req.app.get('deviceId');

  if (
    typeof temperature !== 'number' ||
    typeof humidity !== 'number' ||
    (pressure !== null && typeof pressure !== 'number')
  ) {
    return res.status(400).json({ error: 'Invalid fields' });
  }

  try {
    const info = insertLectura.run({ device_id: deviceId, temperature, humidity, pressure });
    const nuevaLectura = db.prepare('SELECT * FROM lecturas WHERE id = ?').get(info.lastInsertRowid);

    const io = req.app.get('io');
    if (io) {
      io.emit('newData', {
        deviceId,
        temperature,
        humidity,
        pressure,
        timestamp: nuevaLectura.timestamp,
      });
    }

    res.status(201).json({ message: `Data saved for ${deviceId}` });
  } catch (err) {
    console.error('❌ Error in postData:', err);
    res.status(500).json({ error: 'Error saving data' });
  }
};

export const getData = async (req, res) => {
  try {
    const deviceId = req.app.get('deviceId');
    const limit = Number(req.query.limit) || 500;
    const lecturas = selectLecturas.all(deviceId, limit);
    res.json(lecturas);
  } catch (err) {
    console.error('❌ Error in getData:', err);
    res.status(500).json({ error: 'Error fetching readings' });
  }
};
