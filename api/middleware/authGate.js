// sensor/read_loop.py y ml/service.py corren en este mismo Pi y hacen POST directo
// a localhost sin sesión de navegador — se les deja pasar solo si la conexión es
// realmente loopback (sin X-Forwarded-For de por medio, es decir no vienen del
// proxy de Tailscale Funnel).
const RUTAS_INTERNAS = new Set(['/data', '/ml/update']);

function esLoopback(ip) {
  return ip === '127.0.0.1' || ip === '::1' || ip === '::ffff:127.0.0.1';
}

export function authGate(req, res, next) {
  if (req.session?.authenticated) return next();

  if (req.method === 'POST' && RUTAS_INTERNAS.has(req.path) && esLoopback(req.ip)) {
    return next();
  }

  if (req.method === 'GET' && req.accepts(['html', 'json']) === 'html') {
    return res.redirect('/login.html');
  }
  return res.status(401).json({ error: 'Not authenticated' });
}
