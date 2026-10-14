import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { login, logout } from '../Controllers/authController.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const router = express.Router();

router.get('/login.html', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/login.html'));
});
router.post('/login', login);
router.post('/logout', logout);

export default router;
