import '../config/env.js';
import TelegramBot from 'node-telegram-bot-api';

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: false });

bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  console.log('✅ New message received');
  console.log('chat_id:', chatId);
  bot.sendMessage(chatId, `✅ This is your chat_id: ${chatId}`);
});

export default bot;