import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = process.env.SQLITE_PATH || path.join(__dirname, '../../data/blackorbs.db');

fs.mkdirSync(path.dirname(dbPath), { recursive: true });

const db = new Database(dbPath);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

const schema = fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8');
db.exec(schema);

// Migraciones simples para columnas agregadas después de la creación inicial de la tabla.
const columnasMlEstado = new Set(db.prepare('PRAGMA table_info(ml_estado)').all().map((c) => c.name));
for (const [columna, tipo] of [
  ['normalidad_pct', 'REAL'],
  ['forecast_confianza', 'TEXT'],
]) {
  if (!columnasMlEstado.has(columna)) {
    db.exec(`ALTER TABLE ml_estado ADD COLUMN ${columna} ${tipo}`);
  }
}

export default db;
