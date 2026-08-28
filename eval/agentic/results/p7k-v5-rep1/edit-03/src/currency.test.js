import { test } from "node:test";
import assert from "node:assert/strict";
import { convert, formatCents } from "./currency.js";

test("converts usd to itself unchanged", () => {
  assert.equal(convert(100, "usd", "usd"), 100);
});

test("converts usd to brl at 5.4", () => {
  assert.equal(convert(10000, "usd", "brl"), 54000);
});

test("formats cents with a two-digit fraction and uppercase code", () => {
  assert.equal(formatCents(1234, "usd"), "12.34 USD");
});

test("zero-pads small fractions", () => {
  assert.equal(formatCents(5, "brl"), "0.05 BRL");
});

test("keeps whole dollars zero-padded", () => {
  assert.equal(formatCents(100, "eur"), "1.00 EUR");
});

test("formats negative cents", () => {
  assert.equal(formatCents(-250, "usd"), "-2.50 USD");
});
