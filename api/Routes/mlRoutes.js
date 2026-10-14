import express from 'express';
import { updateMlState, getMlState } from '../Controllers/mlController.js';

const router = express.Router();

router.post('/ml/update', updateMlState);
router.get('/ml/state', getMlState);

export default router;
