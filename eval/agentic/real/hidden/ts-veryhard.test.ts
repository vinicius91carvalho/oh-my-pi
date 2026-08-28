// Hidden check for bug/ts-veryhard.
// Copy to: packages/profile/src/conservative-default.hidden.test.ts
// Run:     pnpm --filter @fbj/profile exec vitest run src/conservative-default.hidden.test.ts
import { describe, expect, it } from "vitest";
import { conservativeDefaultAnswer } from "./conservative-default.js";
import { resolveBooleanAnswer } from "./boolean-answer.js";

/**
 * AGENTS.md, "The conservative default": for legal-status questions answer the
 * negative that claims nothing - never a positive without evidence.
 *
 * The evidence for "authorized where this role is based" is a country on the
 * posting that is also in the candidate's work countries. With no posting, or
 * a profile that lists no work countries, there is no evidence, and the answer
 * must be the negative.
 */
describe("authorization where the job is located: no evidence means the negative", () => {
  const Q =
    "Are you legally authorized to work in the country where the job is located?";

  it("takes the negative when no posting is passed at all", () => {
    const d = conservativeDefaultAnswer(Q);
    expect(d).not.toBeNull();
    expect(d!.answer).toMatch(/^No/);
    expect(resolveBooleanAnswer(d!.answer)).toBe("no");
  });

  it("still answers no for the country the role is based in", () => {
    const a = conservativeDefaultAnswer(
      "Are you authorized to work in the country where this role is located?",
    );
    expect(a?.answer).toMatch(/^No/);
  });

  it("takes the negative when the profile lists no work countries", () => {
    for (const location of [
      "San Francisco, CA, United States",
      "Anywhere in the World",
      "Remote",
      null,
    ]) {
      const d = conservativeDefaultAnswer(Q, { location, workCountries: [] });
      expect(d?.answer, `${location}`).toMatch(/^No/);
    }
  });

  it("takes the negative when the posting names no country and is not open", () => {
    const d = conservativeDefaultAnswer(Q, {
      location: "Remote",
      workCountries: ["Brazil"],
    });
    expect(d?.answer).toMatch(/^No/);
  });

  it("still says yes when there IS evidence", () => {
    expect(
      conservativeDefaultAnswer(Q, {
        location: "São Paulo, Brazil",
        workCountries: ["Brazil"],
      })?.answer,
    ).toMatch(/^Yes/);
    expect(
      conservativeDefaultAnswer(Q, {
        location: "Anywhere in the World",
        remoteScope: "worldwide",
        workCountries: ["Brazil"],
      })?.answer,
    ).toMatch(/^Yes/);
  });
});
