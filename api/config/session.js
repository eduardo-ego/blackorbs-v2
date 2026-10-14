import './env.js';
import session from 'express-session';

export const sessionMiddleware = session({
  name: 'blackorbs.sid',
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    sameSite: 'lax',
    secure: 'auto', // Secure cuando llega por HTTPS (Funnel); no exige HTTPS en LAN. Requiere 'trust proxy' en app.js.
    maxAge: 12 * 60 * 60 * 1000, // 12h — evita repetir el PIN todo el tiempo
  },
});
