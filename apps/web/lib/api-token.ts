import { SignJWT } from "jose";

export type ApiUser = {
  googleSub: string;
  email: string;
  name?: string | null;
};

// Must match JWT_AUDIENCE in the API (apps/api/app/config.py).
export const API_AUDIENCE = "hearback-api";

/** Signs a short-lived token that tells FastAPI who the signed-in user is. */
export async function createApiToken(
  user: ApiUser,
  secret: string,
): Promise<string> {
  return new SignJWT({ email: user.email, name: user.name ?? undefined })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(user.googleSub)
    .setAudience(API_AUDIENCE)
    .setIssuedAt()
    .setExpirationTime("5m")
    .sign(new TextEncoder().encode(secret));
}
