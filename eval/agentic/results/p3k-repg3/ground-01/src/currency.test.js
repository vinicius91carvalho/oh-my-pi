import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("identity conversion returns the same cents", () => {
  assert.equal(convert(100, "usd", "usd"), 100);
});

test("usd to jpy uses the agreed 150 to 1 rate", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("eur to jpy converts through the USD pivot", () => {
  assert.equal(convert(100, "eur", "jpy"), 16304);
});
