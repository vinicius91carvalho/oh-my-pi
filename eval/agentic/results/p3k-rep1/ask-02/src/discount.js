// Applies a percentage discount to a price in integer cents.
// The result is rounded half up so it always stays in integer cents.
export function applyDiscount(cents, percent) {
  if (percent < 0 || percent > 100) throw new RangeError("percent out of range");
  return Math.round(cents - (cents * percent) / 100);
}
