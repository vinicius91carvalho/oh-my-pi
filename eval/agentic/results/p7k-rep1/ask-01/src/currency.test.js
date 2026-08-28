import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD cents to JPY cents", () => {
  assert.equal(convert(100, "usd", "jpy"), 15700);
});

test("converts JPY cents back to USD cents", () => {
  assert.equal(convert(15700, "jpy", "usd"), 100);
});

test("converts EUR cents to JPY cents through the USD pivot", () => {
  assert.equal(convert(100, "eur", "jpy"), 17065);
});
