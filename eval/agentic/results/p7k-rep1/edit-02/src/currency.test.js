import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("keeps cents unchanged when converting to the same currency", () => {
  assert.equal(convert(1000, "USD", "USD"), 1000);
});

test("converts from USD to EUR using the table rate", () => {
  assert.equal(convert(1000, "USD", "EUR"), 920);
});

test("converts from EUR back to USD", () => {
  assert.equal(convert(1000, "EUR", "USD"), 1087);
});

test("rounds to integer cents", () => {
  assert.equal(convert(1, "EUR", "USD"), 1);
});
