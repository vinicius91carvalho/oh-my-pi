// Hidden check for task ts-contract.
// Copy to: packages/core/src/user-facing-failure.hidden.test.ts
// Run:     pnpm --filter @fbj/core exec vitest run src/user-facing-failure.hidden.test.ts
import { describe, expect, it } from "vitest";
import { FAILURE_OUTCOMES, type FailureOutcome } from "./failure-outcome.js";
import { presentedState, userFacingFailure } from "./user-facing-failure.js";

/**
 * The new contract: `userFacingFailure` answers with an object, not a string.
 *
 *   { kind: "actionable" | "closed" | "pending",
 *     waitingOn: "candidate" | "nobody" | "us" }
 *
 * The product decision, written out row by row (never derived from the code):
 * - needs_login / needs_answer: the person has a form to open -> candidate.
 * - posting_gone: the employer took it down, nothing to wait for -> nobody.
 * - wall / our_bug / unknown: a deploy fixes it, not a click -> us.
 */
const EXPECTED: Record<
  FailureOutcome,
  { kind: "actionable" | "closed" | "pending"; waitingOn: "candidate" | "nobody" | "us" }
> = {
  needs_login: { kind: "actionable", waitingOn: "candidate" },
  needs_answer: { kind: "actionable", waitingOn: "candidate" },
  posting_gone: { kind: "closed", waitingOn: "nobody" },
  wall: { kind: "pending", waitingOn: "us" },
  our_bug: { kind: "pending", waitingOn: "us" },
  unknown: { kind: "pending", waitingOn: "us" },
};

describe("userFacingFailure returns { kind, waitingOn }", () => {
  it.each(FAILURE_OUTCOMES)("maps %s", (outcome) => {
    const out = userFacingFailure(outcome);
    expect(typeof out).toBe("object");
    expect(out).toEqual(EXPECTED[outcome]);
  });

  it("covers every outcome", () => {
    expect(Object.keys(EXPECTED).sort()).toEqual([...FAILURE_OUTCOMES].sort());
  });
});

describe("presentedState still reads the kind through the new shape", () => {
  it("warm tone only when the candidate can act", () => {
    expect(
      presentedState("error", "We need your login for this platform.").tone,
    ).toBe("warn");
    expect(presentedState("error", "Cloudflare challenge on the apply page").tone).toBe(
      "off",
    );
    expect(presentedState("error", null).key).toBe("pending");
  });
});
