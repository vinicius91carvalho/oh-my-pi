import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("keeps existing usd to brl behavior", () => {
  assert.equal(convert(100, "usd", "brl"), 540);
});

test("converts usd to jpy with no subunit", () => {
  assert.equal(convert(100, "usd", "jpy"), 150);
});

test("converts jpy back to usd without losing a factor of 100", () => {
  assert.equal(convert(150, "jpy", "usd"), 100);
});

test("round trip through usd is stable", () => {
  assert.equal(convert(convert(1234, "usd", "jpy"), "jpy", "usd"), 1234);
});

test("throws on an unknown currency", () => {
  assert.throws(() => convert(100, "usd", "gbp"), RangeError);
});
