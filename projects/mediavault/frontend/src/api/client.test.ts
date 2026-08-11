import { describe, expect, it } from "vitest";
import { buildQuery } from "./client";

describe("buildQuery", () => {
  it("returns an empty string for no params", () => {
    expect(buildQuery({})).toBe("");
  });

  it("skips null and undefined values", () => {
    expect(buildQuery({ a: undefined, b: null, c: "" })).toBe("");
  });

  it("serializes scalars", () => {
    expect(buildQuery({ page: 2, q: "hero" })).toBe("?page=2&q=hero");
  });

  it("repeats array params", () => {
    expect(buildQuery({ tag_ids: ["a", "b"] })).toBe("?tag_ids=a&tag_ids=b");
  });
});
