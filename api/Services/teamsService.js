import '../config/env.js';

const TEAMS_WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL;

const COLOR_POR_MOOD = {
  critical: 'FF5470',
  attention: 'FBB63E',
};

const sendTeamsAlert = async ({ titulo, mensaje, mood }) => {
  if (!TEAMS_WEBHOOK_URL) {
    console.warn('⚠️ TEAMS_WEBHOOK_URL not configured, skipping Teams alert');
    return false;
  }

  const card = {
    '@type': 'MessageCard',
    '@context': 'http://schema.org/extensions',
    themeColor: COLOR_POR_MOOD[mood] || '4D8DFF',
    title: titulo,
    text: mensaje,
  };

  try {
    const resp = await fetch(TEAMS_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(card),
    });
    if (!resp.ok) {
      console.error('❌ Teams responded with an error:', resp.status, await resp.text());
      return false;
    }
    return true;
  } catch (err) {
    console.error('❌ Error sending Teams alert:', err.message);
    return false;
  }
};

export default sendTeamsAlert;
