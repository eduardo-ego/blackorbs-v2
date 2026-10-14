import { Server } from 'socket.io';
import http from 'http';
import app from './app.js';
import { sessionMiddleware } from './config/session.js';

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
});

// Comparte la sesión de express-session con el handshake de Socket.IO para que
// una conexión de socket sin PIN válido no pueda leer datos igual.
io.engine.use(sessionMiddleware);
io.use((socket, next) => {
  if (socket.request.session?.authenticated) return next();
  next(new Error('Not authenticated'));
});

io.on('connection', (socket) => {
  console.log('🔌 Client connected to sockets');
});

app.set('io', io);

const PORT = process.env.PORT || 3001;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Server listening on port ${PORT}`);
});
