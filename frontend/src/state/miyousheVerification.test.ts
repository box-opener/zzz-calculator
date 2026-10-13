import { describe, expect, it } from "vitest";
import { parseGeetestChallenge, parseRecordVerification } from "./miyousheVerification";

describe("user-completed record verification", () => {
  it("retains only a temporary verification handle, excluding credentials", () => {
    const parsed = parseRecordVerification({ verification_id: "x".repeat(43), expires_at: "2026-10-13T08:00:00Z", cookie: "must-not-copy" });
    expect(JSON.stringify(parsed)).not.toContain("must-not-copy");
  });
  it("rejects invalid session handles and timestamps", () => {
    expect(() => parseRecordVerification({ verification_id: "bad", expires_at: "2026-10-13T08:00:00Z" })).toThrow();
    expect(() => parseRecordVerification({ verification_id: "x".repeat(43), expires_at: "bad" })).toThrow();
  });
  it("only accepts an available official challenge, with no offline shortcut", () => {
    const challenge = { schema_version: "zzz-miyoushe-verification-v1", gt: "b".repeat(32), challenge: "a".repeat(32), success: 1, new_captcha: true };
    expect(parseGeetestChallenge(challenge).success).toBe(1);
    expect(() => parseGeetestChallenge({ ...challenge, success: 0 })).toThrow();
    expect(() => parseGeetestChallenge({ ...challenge, challenge: "" })).toThrow();
  });
});
