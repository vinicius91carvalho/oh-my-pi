import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to JPY at the agreed 150 rate", () => {
  assert.equal(convert(10000, "usd", "jpy"), 1500000);
});

test("converts JPY back to USD", () => {
  assert.equal(convert(150, "jpy", "usd"), 1);
});

test("converts JPY to EUR through the USD pivot", () => {
  assert.equal(convert(15000, "jpy", "eur"), 92);
});
