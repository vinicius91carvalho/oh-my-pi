import { test } from "node:test";
import assert from "node:assert/strict";
import { cartTotal } from "./cart.js";

test("sums item subtotals before discount", () => {
  assert.equal(cartTotal([{ cents: 100, qty: 2 }], 0), 200);
});

test("applies the discount to the whole cart", () => {
  assert.equal(cartTotal([{ cents: 100, qty: 3 }, { cents: 250, qty: 1 }], 10), 495);
});
