// app.js
import './config/env.js';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import './db/index.js'; // inicializa el archivo SQLite y crea el esquema si no existe

import dataRoutes from './Routes/dataRoutes.js';
import alertsRoutes from './Routes/alertsRoutes.js';
import mlRoutes from './Routes/mlRoutes.js';
import chatRoutes from './Routes/chatRoutes.js';
import authRoutes from './Routes/authRoutes.js';
import { sessionMiddleware } from './config/session.js';
import { authGate } from './middleware/authGate.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Necesario para que req.ip / req.secure reflejen el cliente real detrás del
// proxy local de Tailscale Funnel (que conecta a Express desde 127.0.0.1).
app.set('trust proxy', 'loopback');

const deviceId = process.env.DEVICE_ID || 'ORBE_001';
app.set('deviceId', deviceId);

app.use(express.json());
app.use(cors({ origin: '*', methods: ['GET', 'POST'] }));
app.use(sessionMiddleware);

app.use(authRoutes); // expone /login.html y POST /login sin requerir sesión

app.use(authGate); // todo lo de abajo requiere haber pasado el PIN

app.use(express.static('public'));

app.use(dataRoutes);
app.use(alertsRoutes);
app.use(mlRoutes);
app.use(chatRoutes);

app.get('/{*any}', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

export default app;
