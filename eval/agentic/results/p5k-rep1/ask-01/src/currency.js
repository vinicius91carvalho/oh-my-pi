// Minor units (cents, or 1 for yen) of each currency per 1 US dollar.
// JPY has no subunit, so its rate is in whole yen.
const RATES = { usd: 100, eur: 92, brl: 540, jpy: 150 };

export function convert(cents, from, to) {
  if (!(from in RATES) || !(to in RATES)) {
    throw new RangeError(`unknown currency: ${from} or ${to}`);
  }
  return Math.round((cents * RATES[to]) / RATES[from]);
}
