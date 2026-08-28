import { test } from "node:test";
import assert from "node:assert/strict";
import { formatCents } from "./currency.js";

test("formats cents with two decimals and an uppercase code", () => {
  assert.equal(formatCents(1234, "usd"), "12.34 USD");
});

test("zero-pads the cents field for whole amounts", () => {
  assert.equal(formatCents(500, "brl"), "5.00 BRL");
});

test("formats zero cents", () => {
  assert.equal(formatCents(0, "usd"), "0.00 USD");
});

test("keeps the sign on negative cents", () => {
  assert.equal(formatCents(-1234, "eur"), "-12.34 EUR");
});
