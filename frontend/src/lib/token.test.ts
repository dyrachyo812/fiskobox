import { beforeEach, describe, expect, it } from "vitest";

import { clearToken, getToken, setToken } from "@/lib/token";

describe("token storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when token is missing", () => {
    expect(getToken()).toBeNull();
  });

  it("stores and reads token", () => {
    setToken("abc.def.ghi");
    expect(getToken()).toBe("abc.def.ghi");
  });

  it("clears token", () => {
    setToken("abc.def.ghi");
    clearToken();
    expect(getToken()).toBeNull();
  });
});
