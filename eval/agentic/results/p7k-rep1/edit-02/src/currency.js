const RATES = { USD: 1, EUR: 0.92, BRL: 5.4 };

export function convert(cents, from, to) {
  return Math.round((cents / RATES[from]) * RATES[to]);
}
