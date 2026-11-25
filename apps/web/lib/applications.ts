import type { Status } from "@/lib/status";

/** One row of GET /applications (mirrors ApplicationOut in the API). */
export type Application = {
  id: string;
  status: Status;
  company_name: string;
  title: string;
  url: string | null;
  source: string;
  applied_at: string;
  last_event_at: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

/** Mirrors ApplicationPage in the API. */
export type ApplicationPage = {
  items: Application[];
  next_cursor: string | null;
};

/** Builds "/applications?status=...&cursor=..." leaving out empty values. */
export function applicationsPath(status?: Status, cursor?: string): string {
  const params = new URLSearchParams();
  if (status !== undefined) {
    params.set("status", status);
  }
  if (cursor !== undefined) {
    params.set("cursor", cursor);
  }
  const query = params.toString();
  return query === "" ? "/applications" : `/applications?${query}`;
}

/** "2026-09-01T00:00:00Z" → "Sep 1, 2026". UTC so server and browser agree. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    dateStyle: "medium",
    timeZone: "UTC",
  });
}
