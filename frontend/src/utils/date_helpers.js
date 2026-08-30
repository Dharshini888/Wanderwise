export const calculateTripDuration = (start, end) => {
  if (!start || !end) return 1;
  const st = new Date(start);
  const en = new Date(end);
  if (isNaN(st) || isNaN(en)) return 1;
  const diffTime = Math.abs(en - st);
  return Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1);
};
