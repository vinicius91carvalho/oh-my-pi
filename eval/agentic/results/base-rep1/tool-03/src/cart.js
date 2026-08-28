import { applyDiscount } from "./discount.js";

export function cartTotal(items, percent) {
  const subtotal = items.reduce((sum, item) => sum + item.cents * item.qty, 0);
  return applyDiscount(subtotal, percent);
}
