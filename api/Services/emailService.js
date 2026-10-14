import '../config/env.js';
import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});

const sendAlertEmail = async (sensor, tipo, valor) => {
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: process.env.EMAIL_TO,
    subject: `${tipo} Alert`,
    text: `Sensor: ${sensor}\n${tipo}: ${valor}`
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log('Email sent');
    return true;
  } catch (error) {
    console.error('Error sending email:', error);
    return false;
  }
};

export default sendAlertEmail;