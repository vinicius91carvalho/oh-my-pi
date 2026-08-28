import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converting to the same currency keeps the amount", () => {
  assert.equal(convert(1234, "usd", "usd"), 1234);
});

test("converts usd to brl with the table rate", () => {
  assert.equal(convert(1000, "usd", "brl"), 5400);
});

test("converts brl to usd with the table rate", () => {
  assert.equal(convert(5400, "brl", "usd"), 1000);
});

test("keeps integer cents on a fractional result", () => {
  assert.equal(convert(101, "usd", "brl"), 545);
});
