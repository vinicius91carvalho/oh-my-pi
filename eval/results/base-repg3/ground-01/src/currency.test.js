import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converting to the same currency is identity", () => {
  assert.equal(convert(1234, "usd", "usd"), 1234);
});

test("usd to jpy uses the agreed 150:1 rate", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("eur to jpy goes through the USD pivot", () => {
  // 100 / 0.92 * 150 = 16304.34... -> 16304
  assert.equal(convert(100, "eur", "jpy"), 16304);
});
