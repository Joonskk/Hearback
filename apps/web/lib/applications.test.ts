import { expect, test } from "vitest";

import { applicationsPath, formatDate } from "@/lib/applications";

test("applicationsPath with no filters", () => {
  expect(applicationsPath()).toBe("/applications");
});

test("applicationsPath with status and cursor", () => {
  expect(applicationsPath("interview", "abc=")).toBe(
    "/applications?status=interview&cursor=abc%3D",
  );
});

test("formatDate shows the UTC date", () => {
  expect(formatDate("2026-09-01T23:30:00Z")).toBe("Sep 1, 2026");
});
