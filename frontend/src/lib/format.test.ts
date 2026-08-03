import { describe, expect, it } from "vitest";

import { formatDate, formatMoney } from "@/lib/format";

describe("formatMoney", () => {
  it("formats value with currency", () => {
    const result = formatMoney(850, "UAH");
    expect(result).toContain("850");
  });

  it("returns dash for null value", () => {
    expect(formatMoney(null, "UAH")).toBe("—");
  });

  it("falls back when currency code is invalid", () => {
    expect(formatMoney(10, "INVALID")).toBe("10 INVALID");
  });

  it("formats amount without currency when currency is null", () => {
    const result = formatMoney(100, null);
    expect(result).toContain("100");
    expect(result).not.toMatch(/RUB|₽|руб/i);
  });
});

describe("formatDate", () => {
  it("formats iso date", () => {
    const result = formatDate("2024-03-15");
    expect(result).not.toBe("—");
    expect(result).not.toBe("2024-03-15");
  });

  it("returns dash for null", () => {
    expect(formatDate(null)).toBe("—");
  });

  it("returns original string for invalid date", () => {
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
});
