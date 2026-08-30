// Format currency based on user settings
export function formatCurrency(amount, currencyCode = null) {
  let currency = currencyCode;
  
  if (!currency) {
    currency = 'USD';
    try {
      const stored = localStorage.getItem('ww_settings');
      if (stored) {
        const settings = JSON.parse(stored);
        if (settings.currency) currency = settings.currency;
      }
    } catch (_) {}
  }

  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function getStoredUserId() {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const u = JSON.parse(userStr);
      if (u && (u.id || u.user_id)) return u.id || u.user_id;
    }
    const token = localStorage.getItem('token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.user_id) return payload.user_id;
      if (payload.id) return payload.id;
      if (payload.sub && !isNaN(Number(payload.sub))) return Number(payload.sub);
    }
  } catch (_) {}
  return null;
}
