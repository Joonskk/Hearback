"use server";

import { apiFetch } from "@/lib/api";
import { applicationsPath, type ApplicationPage } from "@/lib/applications";
import type { Status } from "@/lib/status";

/** Called from the browser's "Load more" button; runs on the server. */
export async function loadMoreApplications(
  status: Status | undefined,
  cursor: string,
): Promise<ApplicationPage> {
  return apiFetch<ApplicationPage>(applicationsPath(status, cursor));
}
