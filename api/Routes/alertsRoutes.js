import express from 'express';
import {
  sendAlertWhats,
  sendAlertTelegram,
  sendAlertEmailController,
  getAlerts,
} from '../Controllers/alertController.js';

const router = express.Router();

router.post('/sendAlertsWhats', sendAlertWhats);
router.post('/sendAlertsTelegram', sendAlertTelegram);
router.post('/sendAlertsEmail', sendAlertEmailController);
router.get('/alerts', getAlerts);

export default router;
