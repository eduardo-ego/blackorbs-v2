# Black Orbs (v2)

Environmental monitoring IoT device built on a Raspberry Pi CM5, combining a real
Machine Learning core (anomaly detection + forecasting) with an LLM-based natural
language interface for chat and alerts. This is the v2 redesign of an earlier
thesis prototype, rebuilt around measurable, evaluable ML instead of asking an LLM
to interpret raw sensor numbers directly.

## Architecture

All components run on the same device and talk to each other over HTTP /
Socket.IO on `localhost`:

```
blackorbs-v2/
├── api/       Express + Socket.IO + SQLite (Node.js) — ingestion, alerts, chat
├── ml/        Anomaly detection + forecasting service (Python)
├── sensor/    Physical sensor read loop (Python)
├── display/   OLED "mood ring" animation (Python)
└── data/      SQLite database file
```

- **`api/`** — Express API with Socket.IO for live updates and SQLite
  (`better-sqlite3`) for persistence. Serves the static frontend in
  `api/public/` (dashboard, charts, PIN login) and exposes `/data`, `/alerts`,
  `/chat`, `/ml/update`, `/ml/state`.
- **`ml/`** — Runs on its own cycle (default 60s): a hybrid anomaly detector
  (EWMA/z-score while the history is short, Isolation Forest once enough
  readings accumulate) and a forecast module (naive persistence, then
  Holt's exponential smoothing with damped trend). Severity thresholds are
  derived from the data's own distribution, not hardcoded. Posts its result
  to the API (`/ml/update`), which is the single source of truth for device
  "mood" (`happy` / `attention` / `critical` / `thinking`).
- **`sensor/`** — Reads an SHT85 temperature/humidity sensor over I2C and
  posts readings to the API on its own interval.
- **`display/`** — Drives a small SSD1306 OLED, rendering a static,
  duty-cycled ring whose style reflects the current ML mood (reading
  directly from SQLite, no HTTP involved).
- **Chat (`chatController.js`)** — The LLM (OpenAI or Claude, selectable
  per request) never computes anomalies or forecasts itself. It only calls
  read-only tools over data already calculated by the ML service, and
  answers in natural language.

## Running

Each Python component (`ml/`, `sensor/`, `display/`) has its own virtualenv
and `requirements.txt`. In production, all four components run as
`systemd` services (`blackorbs-v2-api`, `blackorbs-v2-ml`,
`blackorbs-v2-sensor`, `blackorbs-v2-display`), each with `Restart=always`.

```bash
# API
cd api && npm install
cp .env.example .env   # fill in API keys, APP_PIN, SESSION_SECRET, etc.
npm start

# ML service
cd ml && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python service.py

# Sensor loop / Display — same pattern, see sensor/ and display/
```

## Environment variables

See `api/.env.example` for the full list (LLM provider keys, Twilio/Telegram/
Teams/Email alert credentials, `APP_PIN` for the dashboard's PIN login,
`SESSION_SECRET`, `SQLITE_PATH`, `DEVICE_ID`).

## Database

SQLite schema in `api/db/schema.sql`: `lecturas` (sensor readings), `alertas`
(alerts), `consultas_ia` (chat history), `ml_estado` (current ML state per
device, one row — mood, anomaly score/variable, normality %, forecast and
confidence).

## License

MIT — see [LICENSE](LICENSE).
