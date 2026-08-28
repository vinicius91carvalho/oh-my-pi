import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to JPY at the agreed 150 yen per dollar", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("round-trips JPY back through the USD pivot", () => {
  assert.equal(convert(15000, "jpy", "usd"), 100);
});

test("converts a non-USD origin to JPY through the pivot", () => {
  assert.equal(convert(100, "eur", "jpy"), 16304);
});
