import { test } from "node:test";
import assert from "node:assert/strict";
import { formatCents } from "./currency.js";

test("formats whole cents with a two-digit fraction", () => {
  assert.equal(formatCents(1234, "usd"), "12.34 USD");
});

test("pads single-digit fractions", () => {
  assert.equal(formatCents(105, "eur"), "1.05 EUR");
});

test("formats zero cents", () => {
  assert.equal(formatCents(0, "brl"), "0.00 BRL");
});

test("formats negative cents", () => {
  assert.equal(formatCents(-1234, "usd"), "-12.34 USD");
});
