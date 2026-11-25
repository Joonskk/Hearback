"use client";

import { useState, useTransition } from "react";

import { loadMoreApplications } from "@/app/applications/actions";
import { StatusBadge } from "@/app/applications/status-badge";
import { type Application, formatDate } from "@/lib/applications";
import type { Status } from "@/lib/status";

type Props = {
  initialItems: Application[];
  initialCursor: string | null;
  status: Status | undefined;
};

export function ApplicationTable({
  initialItems,
  initialCursor,
  status,
}: Props) {
  const [items, setItems] = useState(initialItems);
  const [cursor, setCursor] = useState(initialCursor);
  const [isPending, startTransition] = useTransition();

  function loadMore() {
    if (cursor === null) {
      return;
    }
    startTransition(async () => {
      const page = await loadMoreApplications(status, cursor);
      setItems((current) => [...current, ...page.items]);
      setCursor(page.next_cursor);
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-zinc-500">
          <tr>
            <th className="py-2">Company</th>
            <th className="py-2">Title</th>
            <th className="py-2">Applied</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((application) => (
            <tr key={application.id} className="border-b">
              <td className="py-2 font-medium">{application.company_name}</td>
              <td className="py-2">{application.title}</td>
              <td className="py-2">{formatDate(application.applied_at)}</td>
              <td className="py-2">
                <StatusBadge status={application.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {cursor !== null && (
        <button
          type="button"
          onClick={loadMore}
          disabled={isPending}
          className="self-center rounded-full border px-4 py-2 text-sm disabled:opacity-50"
        >
          {isPending ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
