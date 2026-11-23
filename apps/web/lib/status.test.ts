import { expect, test } from "vitest";

import { STATUSES, statusLabel } from "@/lib/status";

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
