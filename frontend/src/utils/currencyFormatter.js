/**
 * currencyFormatter.js — WanderWise Global Currency Utility (v2.7.2)
 *
 * Usage:
 *   formatMoney(700, 'INR')  → '₹58,450'
 *   formatMoney(700, 'AED')  → 'AED 2,569'
 *   formatMoney(700, 'EUR')  → '€644'
 *   getBudgetDisplay(dest.budget)  → uses formatted field from API
 */

/**
 * Format a numeric amount into a localized currency string.
 * Uses the Intl.NumberFormat API for proper locale formatting.
 *
 * @param {number} amount - Numeric amount to format
 * @param {string} currency - ISO 4217 currency code (e.g. 'INR', 'USD', 'AED')
 * @returns {string} Formatted currency string
 */
export function formatMoney(amount, currency = 'USD') {
  if (amount === null || amount === undefined || isNaN(amount)) return '--';
  const code = (currency || 'USD').toUpperCase();

  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: code,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    // Fallback: use symbol-only formatting for unrecognized codes
    return `${code} ${Number(amount).toLocaleString()}`;
  }
}

export const formatCurrency = formatMoney;

/**
 * Extract a display string from a budget object returned by the API.
 * Supports both the new structured format and legacy flat format.
 *
 * New format:  { formatted: '₹58,450', converted_amount: 58450, user_currency: 'INR' }
 * Legacy:      { average_budget: 700 }  → falls back to USD display
 *
 * @param {object|number|null} budgetObj - Budget field from API response
 * @param {string} fallbackCurrency - Currency to use if budgetObj is a plain number
 * @returns {string} Formatted budget string
 */
export function getBudgetDisplay(budgetObj, fallbackCurrency = 'USD') {
  if (!budgetObj) return '--';

  // New structured format from backend
  if (typeof budgetObj === 'object') {
    if (budgetObj.formatted) return budgetObj.formatted;
    if (budgetObj.converted_amount != null && budgetObj.user_currency) {
      return formatMoney(budgetObj.converted_amount, budgetObj.user_currency);
    }
    if (budgetObj.amount != null && budgetObj.base_currency) {
      return formatMoney(budgetObj.amount, budgetObj.base_currency);
    }
  }

  // Legacy: plain number
  if (typeof budgetObj === 'number') {
    return formatMoney(budgetObj, fallbackCurrency);
  }

  return String(budgetObj);
}

/**
 * Get the currency symbol for a given ISO code.
 * Uses a local lookup table for common currencies;
 * falls back to the code itself for unknown ones.
 *
 * @param {string} code - ISO 4217 currency code
 * @returns {string} Currency symbol
 */
export function getCurrencySymbol(code) {
  const SYMBOLS = {
    USD: '$', INR: '₹', EUR: '€', GBP: '£', JPY: '¥', AUD: 'A$',
    CAD: 'C$', CHF: 'CHF', CNY: '¥', SGD: 'S$', HKD: 'HK$', NZD: 'NZ$',
    SEK: 'kr', NOK: 'kr', DKK: 'kr.', AED: 'د.إ', SAR: '﷼', QAR: 'ر.ق',
    KWD: 'د.ك', OMR: 'ر.ع.', BHD: '.د.ب', EGP: 'E£', TRY: '₺', ILS: '₪',
    ZAR: 'R', BRL: 'R$', MXN: '$', MYR: 'RM', THB: '฿', IDR: 'Rp',
    PHP: '₱', VND: '₫', KRW: '₩', PKR: '₨', BDT: '৳', NGN: '₦',
    KES: 'KSh', TWD: 'NT$', PLN: 'zł', HUF: 'Ft', CZK: 'Kč', UAH: '₴',
    RON: 'lei', BGN: 'лв', RUB: '₽', TRY: '₺',
  };
  return SYMBOLS[(code || '').toUpperCase()] || code || '$';
}

/**
 * Validate that a string is a plausible ISO 4217 currency code (3 uppercase letters).
 * @param {string} code
 * @returns {boolean}
 */
export function isValidCurrencyCode(code) {
  return typeof code === 'string' && /^[A-Z]{3}$/.test(code.toUpperCase());
}

/**
 * Parse a currency code from a string like "USD ($)" → "USD"
 * @param {string} raw
 * @returns {string}
 */
export function parseCurrencyCode(raw) {
  if (!raw) return 'USD';
  const parts = raw.trim().split(' ');
  const code = parts[0].toUpperCase();
  return /^[A-Z]{3}$/.test(code) ? code : 'USD';
}
