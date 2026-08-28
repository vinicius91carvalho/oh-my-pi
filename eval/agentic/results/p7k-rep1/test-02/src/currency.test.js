import { test } from "node:test";
import assert from "node:assert/strict";
import { convert } from "./currency.js";

test("converts USD to BRL in integer cents", () => {
  assert.equal(convert(1000, "USD", "BRL"), 5400);
});

test("converts EUR to USD in integer cents", () => {
  assert.equal(convert(1000, "EUR", "USD"), 1087);
});
