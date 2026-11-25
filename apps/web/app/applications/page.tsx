import Link from "next/link";
import { Suspense } from "react";

import { ApplicationTable } from "@/app/applications/application-table";
import { apiFetch } from "@/lib/api";
import { applicationsPath, type ApplicationPage } from "@/lib/applications";
import { parseStatus, type Status, STATUSES, statusLabel } from "@/lib/status";

export default function ApplicationsPage({
  searchParams,
}: PageProps<"/applications">) {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-8">
      <h1 className="text-2xl font-semibold">My applications</h1>
      <Suspense fallback={<p>Loading…</p>}>
        <ApplicationList searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function ApplicationList({
  searchParams,
}: {
  searchParams: PageProps<"/applications">["searchParams"];
}) {
  const status = parseStatus((await searchParams).status);
  const page = await apiFetch<ApplicationPage>(applicationsPath(status));

  return (
    <>
      <StatusFilter current={status} />
      {page.items.length === 0 ? (
        <p className="text-zinc-500">
          {status === undefined
            ? "No applications yet."
            : `No applications with status "${statusLabel(status)}".`}
        </p>
      ) : (
        <ApplicationTable
          // A new key resets the table's state when the filter changes.
          key={status ?? "all"}
          initialItems={page.items}
          initialCursor={page.next_cursor}
          status={status}
        />
      )}
    </>
  );
}

function StatusFilter({ current }: { current: Status | undefined }) {
  const options: { label: string; status: Status | undefined }[] = [
    { label: "All", status: undefined },
    ...STATUSES.map((status) => ({ label: statusLabel(status), status })),
  ];

  return (
    <nav className="flex flex-wrap gap-2 text-sm">
      {options.map((option) => (
        <Link
          key={option.label}
          href={applicationsPath(option.status)}
          className={`rounded-full border px-3 py-1 ${
            option.status === current ? "bg-black text-white" : ""
          }`}
        >
          {option.label}
        </Link>
      ))}
    </nav>
  );
}
