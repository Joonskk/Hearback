import { expect, test } from "vitest";

import { ApiError, readResponse } from "@/lib/api-error";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status });
}

/** Runs readResponse and returns the ApiError it throws. */
async function readError(response: Response): Promise<ApiError> {
  try {
    await readResponse(response);
  } catch (error) {
    if (error instanceof ApiError) {
      return error;
    }
    throw error;
  }
  throw new Error("Expected readResponse to throw");
}

test("2xx returns the JSON body", async () => {
  const body = await readResponse(
    jsonResponse(200, { email: "a@example.com" }),
  );
  expect(body).toEqual({ email: "a@example.com" });
});

test("204 returns undefined", async () => {
  const body = await readResponse(new Response(null, { status: 204 }));
  expect(body).toBeUndefined();
});

test("API error shape becomes an ApiError", async () => {
  const error = await readError(
    jsonResponse(409, {
      error: {
        code: "duplicate_application",
        message: "You already logged this job",
      },
    }),
  );

  expect(error.status).toBe(409);
  expect(error.code).toBe("duplicate_application");
  expect(error.message).toBe("You already logged this job");
});

test("non-JSON error still becomes an ApiError", async () => {
  const error = await readError(
    new Response("Bad Gateway", { status: 502, statusText: "Bad Gateway" }),
  );

  expect(error.status).toBe(502);
  expect(error.code).toBe("unknown_error");
});
