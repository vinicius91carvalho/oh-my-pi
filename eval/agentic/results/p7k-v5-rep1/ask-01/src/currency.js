const RATES = { usd: 1, eur: 0.92, brl: 5.4, jpy: 159.6 };

export function convert(cents, from, to) {
  return Math.round((cents / RATES[from]) * RATES[to]);
}
