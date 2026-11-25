import { expect, test } from "vitest";

import {
  parseStatus,
  STATUS_COLORS,
  STATUSES,
  statusLabel,
} from "@/lib/status";

test("statusLabel capitalizes the status", () => {
  expect(statusLabel("interview")).toBe("Interview");
});

test("statusLabel has a label for every status", () => {
  expect(STATUSES.map(statusLabel)).toEqual([
    "Applied",
    "Assessment",
    "Interview",
    "Offer",
    "Rejected",
    "Stale",
  ]);
});

test("each status has the color from the design doc", () => {
  expect(STATUS_COLORS.applied).toContain("zinc");
  expect(STATUS_COLORS.assessment).toContain("zinc");
  expect(STATUS_COLORS.interview).toContain("green");
  expect(STATUS_COLORS.offer).toContain("green");
  expect(STATUS_COLORS.rejected).toContain("red");
  expect(STATUS_COLORS.stale).toContain("yellow");
});

test("parseStatus accepts only real statuses", () => {
  expect(parseStatus("interview")).toBe("interview");
  expect(parseStatus("hired")).toBeUndefined();
  expect(parseStatus(undefined)).toBeUndefined();
  expect(parseStatus(["interview", "offer"])).toBeUndefined();
});
