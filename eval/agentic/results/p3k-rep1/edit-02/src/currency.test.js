import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("identity conversion keeps cents unchanged", () => {
  assert.equal(convert(100, "usd", "usd"), 100);
});

test("converts usd to eur", () => {
  assert.equal(convert(100, "usd", "eur"), 92);
});

test("converts usd to brl", () => {
  assert.equal(convert(100, "usd", "brl"), 540);
});

test("converts eur back to usd", () => {
  assert.equal(convert(100, "eur", "usd"), 109);
});

test("keeps integer cents on a fractional result", () => {
  assert.equal(convert(999, "usd", "brl"), 5395);
});

test("rounds a sub-cent result up to the nearest cent", () => {
  assert.equal(convert(1, "usd", "eur"), 1);
});
