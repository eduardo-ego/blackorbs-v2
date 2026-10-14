const MAX_INTENTOS = 8;
const VENTANA_MS = 10 * 60 * 1000; // 10 min

// Contador simple en memoria por IP. Se reinicia si reinicia el proceso — suficiente
// para frenar fuerza bruta casual contra un PIN corto, no es protección de grado industrial.
const intentosPorIp = new Map();

function estaBloqueada(ip) {
  const registro = intentosPorIp.get(ip);
  if (!registro) return false;
  if (Date.now() - registro.desde > VENTANA_MS) {
    intentosPorIp.delete(ip);
    return false;
  }
  return registro.count >= MAX_INTENTOS;
}

function registrarIntentoFallido(ip) {
  const registro = intentosPorIp.get(ip);
  if (!registro || Date.now() - registro.desde > VENTANA_MS) {
    intentosPorIp.set(ip, { count: 1, desde: Date.now() });
  } else {
    registro.count += 1;
  }
}

export const login = (req, res) => {
  const ip = req.ip;

  if (estaBloqueada(ip)) {
    return res.status(429).json({ error: 'Too many attempts. Wait a few minutes and try again.' });
  }

  const { pin } = req.body;
  const pinCorrecto = process.env.APP_PIN;

  if (typeof pin !== 'string' || pin !== pinCorrecto) {
    registrarIntentoFallido(ip);
    return res.status(401).json({ error: 'Incorrect code' });
  }

  intentosPorIp.delete(ip);
  req.session.authenticated = true;
  res.json({ ok: true });
};

export const logout = (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
};
