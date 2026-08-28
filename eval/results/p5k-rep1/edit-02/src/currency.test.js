import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converting within the same currency keeps the value", () => {
  assert.equal(convert(1000, "usd", "usd"), 1000);
});

test("converts using the exchange rates", () => {
  assert.equal(convert(1000, "usd", "eur"), 920);
  assert.equal(convert(1000, "usd", "brl"), 5400);
});

test("keeps integer cents on a fractional result", () => {
  // 100 usd cents -> brl: 100 / 1 * 5.4 = 540, exact.
  assert.equal(convert(1, "usd", "brl"), 5);
  // 7 usd cents -> brl: 7 * 5.4 = 37.8, rounds to 38.
  assert.equal(convert(7, "usd", "brl"), 38);
});
