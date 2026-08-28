const RATES = { usd: 1, eur: 0.92, brl: 5.4 };

export function convert(cents, from, to) {
  return Math.round((cents / RATES[from]) * RATES[to]);
}

// Formats integer cents as a major-unit string, e.g. 1234 -> "12.34 USD".
export function formatCents(cents, code) {
  const c = String(code).toUpperCase();
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")} ${c}`;
}
