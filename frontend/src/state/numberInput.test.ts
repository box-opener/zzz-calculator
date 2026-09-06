import { describe, expect, it } from "vitest";
import {
  cancelNumberDraft,
  commitNumberDraft,
  createNumberDraftState,
  syncExternalNumberValue,
  updateNumberDraft,
} from "./numberInput";

describe("number draft state", () => {
  it("keeps a backspace draft empty without committing zero", () => {
    const draft = updateNumberDraft(createNumberDraftState(12), "");
    expect(draft.draft).toBe("");
    const result = commitNumberDraft(draft);
    expect(result.changed).toBe(false);
    expect(result.value).toBe(12);
    expect(result.state.draft).toBe("12");
  });

  it("allows a decimal to be typed continuously and commits it once", () => {
    let draft = createNumberDraftState(1);
    draft = updateNumberDraft(draft, "1.");
    draft = updateNumberDraft(draft, "1.25");
    const first = commitNumberDraft(draft);
    expect(first.value).toBe(1.25);
    expect(first.changed).toBe(true);
    const second = commitNumberDraft(first.state);
    expect(second.value).toBe(1.25);
    expect(second.changed).toBe(false);
  });

  it("accepts negative intermediate text but rejects it at a non-negative boundary", () => {
    const draft = updateNumberDraft(createNumberDraftState(3), "-");
    expect(draft.draft).toBe("-");
    const result = commitNumberDraft(draft, { min: 0 });
    expect(result.value).toBe(3);
    expect(result.state.draft).toBe("3");
  });

  it("rejects empty, fractional integers, and out-of-range values on commit", () => {
    expect(commitNumberDraft(updateNumberDraft(createNumberDraftState(4), ""), { integer: true }).value).toBe(4);
    expect(commitNumberDraft(updateNumberDraft(createNumberDraftState(4), "4.5"), { integer: true }).value).toBe(4);
    expect(commitNumberDraft(updateNumberDraft(createNumberDraftState(4), "9"), { min: 1, max: 6 }).value).toBe(4);
  });

  it("cancels to the last committed value and syncs external updates", () => {
    const edited = updateNumberDraft(createNumberDraftState(8), "20");
    expect(cancelNumberDraft(edited)).toEqual({ draft: "8", committed: 8 });
    expect(syncExternalNumberValue(16)).toEqual({ draft: "16", committed: 16 });
    expect(syncExternalNumberValue(null)).toEqual({ draft: "", committed: null });
  });
});
