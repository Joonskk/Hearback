import { STATUS_COLORS, type Status, statusLabel } from "@/lib/status";

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
    >
      {statusLabel(status)}
    </span>
  );
}
