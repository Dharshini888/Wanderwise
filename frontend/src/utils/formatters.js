// Format currency based on user settings
export function formatCurrency(amount, currencyCode = null) {
  let currency = currencyCode;
  
  if (!currency) {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const u = JSON.parse(userStr);
        if (u && u.currency) currency = u.currency;
      }
    } catch (_) {}
  }

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


export function formatTripDate(dateInput, formatType = 'medium') {
  if (!dateInput) return '';
  try {
    const str = String(dateInput).split('T')[0];
    const parts = str.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      if (formatType === 'short') {
        return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
      }
      if (formatType === 'weekday') {
        return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
      }
      if (formatType === 'full') {
        return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
      }
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }
    const d = new Date(dateInput);
    return isNaN(d.getTime()) ? String(dateInput) : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch (_) {
    return String(dateInput);
  }
}
