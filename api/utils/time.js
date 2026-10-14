const ZONA_HORARIA = 'America/Mexico_City';

export function formatearLocal(isoString) {
  if (!isoString) return null;
  return new Date(isoString).toLocaleString('en-US', {
    timeZone: ZONA_HORARIA,
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
