import { describe, expect, it } from "vitest";
import { formatBytes, initials } from "./format";

describe("formatBytes", () => {
  it("formats zero", () => {
    expect(formatBytes(0)).toBe("0 B");
  });

  it("formats bytes and kilobytes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
  });

  it("formats megabytes", () => {
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});

describe("initials", () => {
  it("uses the full name when present", () => {
    expect(initials("Ada Lovelace", "ada@example.com")).toBe("AL");
  });

  it("falls back to the email", () => {
    expect(initials("", "jordan@studio.com")).toBe("JS");
  });
});
