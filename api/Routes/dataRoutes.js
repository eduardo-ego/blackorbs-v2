import express from 'express';
import { postData, getData } from '../Controllers/dataController.js';

const router = express.Router();

router.post('/data', postData);
router.get('/data', getData);

export default router;
