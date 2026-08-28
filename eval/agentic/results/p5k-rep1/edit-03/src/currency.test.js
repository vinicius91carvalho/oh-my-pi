import { test } from "node:test";
import assert from "node:assert/strict";
import { convert, formatCents } from "./currency.js";

test("converts between currencies", () => {
  assert.equal(convert(100, "usd", "brl"), 540);
});

test("formats cents with a two-digit minor part", () => {
  assert.equal(formatCents(1234, "usd"), "12.34 USD");
});

test("pads minor part to two digits", () => {
  assert.equal(formatCents(5, "brl"), "0.05 BRL");
});

test("normalizes the currency code to uppercase", () => {
  assert.equal(formatCents(100, "eur"), "1.00 EUR");
});

test("keeps the sign on negative cents", () => {
  assert.equal(formatCents(-250, "USD"), "-2.50 USD");
});
