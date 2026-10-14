CREATE TABLE IF NOT EXISTS lecturas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT NOT NULL,
  temperature REAL,
  humidity REAL,
  pressure REAL,
  timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_lecturas_device_ts ON lecturas(device_id, timestamp);

CREATE TABLE IF NOT EXISTS alertas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT,
  type TEXT,
  value REAL,
  threshold REAL,
  unit TEXT,
  location TEXT,
  timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  severity TEXT,
  status TEXT,
  message TEXT
);
CREATE INDEX IF NOT EXISTS idx_alertas_device_ts ON alertas(device_id, timestamp);

CREATE TABLE IF NOT EXISTS consultas_ia (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT,
  modelo TEXT,
  prompt TEXT,
  respuesta TEXT,
  timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_consultas_device_ts ON consultas_ia(device_id, timestamp);

-- Estado actual (uno por dispositivo) calculado por el servicio de ML.
-- El LLM del chat solo LEE esta tabla, nunca calcula anomalías/forecast por si mismo.
CREATE TABLE IF NOT EXISTS ml_estado (
  device_id TEXT PRIMARY KEY,
  mood TEXT NOT NULL DEFAULT 'happy',          -- happy | attention | critical | thinking
  anomaly_score REAL,
  anomaly_variable TEXT,
  normalidad_pct REAL,                          -- 0-100, qué tan "normal" es la lectura actual
  forecast_temperature REAL,
  forecast_humidity REAL,
  forecast_horizon_minutes INTEGER,
  forecast_confianza TEXT,                      -- high | low
  message TEXT,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
