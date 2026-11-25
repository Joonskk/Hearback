import { decodeProtectedHeader, jwtVerify } from "jose";
import { expect, test } from "vitest";

import { API_AUDIENCE, createApiToken } from "@/lib/api-token";

const SECRET = "test-secret";
const USER = { googleSub: "google-123", email: "a@example.com", name: "A" };

async function verify(token: string, secret: string) {
  return jwtVerify(token, new TextEncoder().encode(secret), {
    audience: API_AUDIENCE,
  });
}

test("token carries the user's claims and the API audience", async () => {
  const token = await createApiToken(USER, SECRET);

  const { payload } = await verify(token, SECRET);

  expect(payload.sub).toBe("google-123");
  expect(payload.email).toBe("a@example.com");
  expect(payload.name).toBe("A");
  expect(payload.aud).toBe("hearback-api");
});

test("token is signed with HS256 and expires in 5 minutes", async () => {
  const token = await createApiToken(USER, SECRET);

  const { payload } = await verify(token, SECRET);

  expect(decodeProtectedHeader(token).alg).toBe("HS256");
  expect(payload.exp! - payload.iat!).toBe(300);
});

test("token signed with another secret is rejected", async () => {
  const token = await createApiToken(USER, "other-secret");

  await expect(verify(token, SECRET)).rejects.toThrow();
});
