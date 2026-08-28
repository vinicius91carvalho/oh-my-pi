import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converting to the same currency is identity", () => {
  assert.equal(convert(100, "usd", "usd"), 100);
});

test("converts USD to JPY at the agreed 150:1 rate", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("routes EUR to JPY through the USD pivot", () => {
  assert.equal(convert(100, "eur", "jpy"), 16304);
});
