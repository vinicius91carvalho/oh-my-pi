const RATES = { usd: 1, eur: 0.92, brl: 5.4 };

export function convert(cents, from, to) {
  return Math.round((cents / RATES[from]) * RATES[to]);
}
