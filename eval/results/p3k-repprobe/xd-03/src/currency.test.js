import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to JPY at 150 ienes per dollar", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("converts JPY back to USD through the pivot", () => {
  assert.equal(convert(15000, "jpy", "usd"), 100);
});

test("keeps integer cents on a fractional conversion", () => {
  assert.equal(convert(1, "usd", "eur"), 1);
});
