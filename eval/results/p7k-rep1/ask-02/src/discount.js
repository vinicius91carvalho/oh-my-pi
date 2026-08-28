// Applies a percentage discount to a price in integer cents.
// Money is integer cents everywhere (project rule): the result is rounded to a whole cent.
export function applyDiscount(cents, percent) {
  if (percent < 0 || percent > 100) throw new RangeError("percent out of range");
  return Math.round(cents - (cents * percent) / 100);
}
