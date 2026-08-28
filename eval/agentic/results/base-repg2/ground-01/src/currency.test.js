import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to JPY at the agreed rate", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("round-trips JPY back to USD", () => {
  assert.equal(convert(15000, "jpy", "usd"), 100);
});

test("converts JPY to BRL through the USD pivot", () => {
  assert.equal(convert(15000, "jpy", "brl"), 540);
});
