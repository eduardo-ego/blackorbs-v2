import express from 'express';
import { chat, getChatHistory } from '../Controllers/chatController.js';

const router = express.Router();

router.post('/chat', chat);
router.get('/chat/history', getChatHistory);

export default router;
