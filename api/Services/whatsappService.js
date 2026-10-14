import '../config/env.js';
import twilio from 'twilio';

const client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);

const sendAlert = async (toPhone, temperature, humidity, sensor) => {
  const message = `⚠️ Alert\nSensor: ${sensor}\nTemperature: ${temperature}°C\nHumidity: ${humidity}%`;
  try {
    const response = await client.messages.create({
      from: process.env.TWILIO_WHATSAPP_FROM,
      to: `whatsapp:${toPhone}`,
      body: message
    });
    console.log('Message sent:', response.sid);
  } catch (error) {
    console.error('Error sending message:', error.message);
  }
};

export default sendAlert;