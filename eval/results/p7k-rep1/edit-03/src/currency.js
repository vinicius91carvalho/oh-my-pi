const RATES = { usd: 1, eur: 0.92, brl: 5.4 };

export function convert(cents, from, to) {
  return Math.round((cents / RATES[from]) * RATES[to]);
}

// Formats integer cents as "12.34 USD" style output.
export function formatCents(cents, code) {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  const whole = Math.floor(abs / 100);
  const frac = String(abs % 100).padStart(2, "0");
  return `${sign}${whole}.${frac} ${code.toUpperCase()}`;
}
