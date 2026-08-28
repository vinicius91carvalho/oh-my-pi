import { test } from "node:test";
import assert from "node:assert/strict";
import { applyDiscount } from "./discount.js";

test("applies a round discount", () => {
  assert.equal(applyDiscount(1000, 10), 900);
});

test("keeps integer cents on a fractional discount", () => {
  assert.equal(applyDiscount(999, 10), 899);
});
