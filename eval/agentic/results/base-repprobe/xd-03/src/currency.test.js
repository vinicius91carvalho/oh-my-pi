import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts between supported currencies in integer cents", () => {
  assert.equal(convert(100, "usd", "eur"), 92);
  assert.equal(convert(100, "usd", "jpy"), 15500);
  assert.equal(convert(100, "jpy", "usd"), 1);
  assert.equal(convert(100, "brl", "usd"), 19);
});
