import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to JPY", () => {
  assert.equal(convert(100, "usd", "jpy"), 15000);
});

test("converts JPY to USD", () => {
  assert.equal(convert(15000, "jpy", "usd"), 100);
});

test("keeps integer cents through a JPY conversion", () => {
  assert.equal(typeof convert(1, "usd", "jpy"), "number");
  assert.equal(convert(1, "usd", "jpy"), 150);
});

test("round trips JPY through the USD pivot", () => {
  assert.equal(convert(convert(12345, "usd", "jpy"), "jpy", "usd"), 12345);
});

test("converts JPY to BRL via the USD pivot", () => {
  assert.equal(convert(15000, "jpy", "brl"), 540);
});
