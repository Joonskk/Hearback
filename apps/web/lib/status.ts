export const STATUSES = [
  "applied",
  "assessment",
  "interview",
  "offer",
  "rejected",
  "stale",
] as const;

export type Status = (typeof STATUSES)[number];

export function statusLabel(status: Status): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/** Tailwind classes for each status badge (design doc 6.4). */
export const STATUS_COLORS: Record<Status, string> = {
  applied: "bg-zinc-100 text-zinc-700",
  assessment: "bg-zinc-100 text-zinc-700",
  interview: "bg-green-100 text-green-800",
  offer: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  stale: "bg-yellow-100 text-yellow-800",
};

/** Turns a ?status= value from the URL into a Status, or undefined if it isn't one. */
export function parseStatus(value: unknown): Status | undefined {
  return STATUSES.find((status) => status === value);
}
