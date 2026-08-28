import { test } from "node:test";
import assert from "node:assert/strict";
import { formatCents } from "./currency.js";

test("formats cents as major units with an uppercase code", () => {
  assert.equal(formatCents(1234, "usd"), "12.34 USD");
});

test("pads small amounts with zeros", () => {
  assert.equal(formatCents(5, "BRL"), "0.05 BRL");
});

test("formats zero and negative amounts", () => {
  assert.equal(formatCents(0, "eur"), "0.00 EUR");
  assert.equal(formatCents(-1234, "USD"), "-12.34 USD");
});
