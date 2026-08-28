import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD cents to JPY cents", () => {
  // 100 USD = 15960 yen at 159.6; 10000 USD cents -> 1596000 JPY cents.
  assert.equal(convert(10000, "usd", "jpy"), 1596000);
});

test("converts JPY back to USD without drift", () => {
  assert.equal(convert(1596000, "jpy", "usd"), 10000);
});

test("converts through the USD pivot into JPY", () => {
  // 1 EUR -> (1 / 0.92) USD -> 173.4782... yen -> 17348 JPY cents.
  assert.equal(convert(100, "eur", "jpy"), 17348);
});

test("converts JPY to BRL through the USD pivot", () => {
  // 15960 yen = 100 USD cents -> 540 BRL cents at 5.4.
  assert.equal(convert(15960, "jpy", "brl"), 540);
});
