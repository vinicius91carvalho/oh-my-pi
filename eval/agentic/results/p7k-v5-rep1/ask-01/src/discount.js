// Applies a percentage discount to a price in integer cents.
export function applyDiscount(cents, percent) {
  if (percent < 0 || percent > 100) throw new RangeError("percent out of range");
  // Rounding rule: "round half up" (see docs/decisions.md, 2026-05-02).
  return Math.round(cents - (cents * percent) / 100);
}
