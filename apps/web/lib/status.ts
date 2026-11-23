export const STATUSES = ["applied", "assessment", "interview", "offer", "rejected", "stale"] as const;

export type Status = (typeof STATUSES)[number];

export function statusLabel(status: Status): string {
    return status.charAt(0).toUpperCase() + status.slice(1);
}
