import "server-only";

import { connection } from "next/server";

import { auth } from "@/auth";
import { ApiError, readResponse } from "@/lib/api-error";
import { createApiToken } from "@/lib/api-token";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`Missing environment variable ${name}`);
  }
  return value;
}

/** Calls FastAPI as the signed-in user. Server-side only: the token never reaches the browser. */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  // Mark this render as request-time before Auth.js re-encrypts the session cookie.
  await connection();

  const session = await auth();
  if (session === null) {
    throw new ApiError(401, "not_signed_in", "Not signed in");
  }
  const { googleSub, email, name } = session.user;
  if (typeof email !== "string") {
    throw new ApiError(401, "not_signed_in", "Session has no email");
  }

  const token = await createApiToken(
    { googleSub, email, name },
    requireEnv("JWT_SECRET"),
  );
  const response = await fetch(`${requireEnv("API_URL")}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  return readResponse<T>(response);
}
