import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converting to the same currency is a no-op", () => {
  assert.equal(convert(100, "USD", "USD"), 100);
});

test("converts USD to EUR at the configured rate", () => {
  assert.equal(convert(100, "USD", "EUR"), 92);
});

test("converts EUR to USD at the configured rate", () => {
  assert.equal(convert(100, "EUR", "USD"), 109);
});

test("converts USD to BRL at the configured rate", () => {
  assert.equal(convert(100, "USD", "BRL"), 540);
});

test("routes cross-currency conversions through USD as pivot", () => {
  assert.equal(convert(100, "EUR", "BRL"), 587);
});

test("returns integer cents", () => {
  assert.ok(Number.isInteger(convert(999, "EUR", "BRL")));
});
