import { describe, expect, it } from "vitest";
import { parseQrSnapshot } from "./miyousheQr";

const snapshot = { schema_version: "zzz-miyoushe-qr-v1", status: "created", expires_at: "2026-10-13T08:00:00Z",
  poll_after_ms: 2000, accounts: [], account_warning: false, session_id: "x".repeat(43), qr_image: "data:image/svg+xml;base64,PHN2Zz4=" };

describe("volatile QR login state", () => {
  it("keeps only the local QR image and login handle, discarding extra cookie fields", () => {
    const parsed = parseQrSnapshot({ ...snapshot, cookie: "do-not-copy", accounts: [{ uid: "12345678", nickname: "绳匠", ltoken: "do-not-copy" }] }, true);
    expect(parsed.session_id).toBe(snapshot.session_id);
    expect(JSON.stringify(parsed)).not.toContain("do-not-copy");
  });
  it("does not accept remote QR images or malformed session handles", () => {
    expect(() => parseQrSnapshot({ ...snapshot, qr_image: "https://example.com/qr.png" }, true)).toThrow();
    expect(() => parseQrSnapshot({ ...snapshot, session_id: "invalid" }, true)).toThrow();
  });
  it("discards the QR image and handle from confirmed status responses", () => {
    const parsed = parseQrSnapshot({ ...snapshot, status: "confirmed", accounts: [{ uid: "12345678", nickname: "绳匠" }] });
    expect(parsed.status).toBe("confirmed");
    expect(parsed.qr_image).toBeUndefined();
    expect(parsed.session_id).toBeUndefined();
  });
  it("rejects incompatible schema and unsafe polling intervals", () => {
    expect(() => parseQrSnapshot({ ...snapshot, schema_version: "old" })).toThrow();
    expect(() => parseQrSnapshot({ ...snapshot, poll_after_ms: 0 })).toThrow();
  });
});
