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
