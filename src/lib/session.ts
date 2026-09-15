import { SignJWT, jwtVerify } from "jose";
import { isRole, type Role } from "./rbac";

/**
 * Session token handling only. This module is imported by `middleware.ts`, so
 * it must stay Edge-compatible: no Mongoose, no bcrypt, no `next/headers`.
 */

export const SESSION_COOKIE = "arg_session";
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 8; // one working day

export type SessionPayload = {
  sub: string;
  name: string;
  email: string;
  role: Role;
};

function secretKey(): Uint8Array {
  const secret = process.env.SESSION_SECRET;

  if (!secret || secret.length < 32) {
    throw new Error(
      "SESSION_SECRET must be set to a random string of at least 32 characters. Generate one with: openssl rand -base64 32",
    );
  }

  return new TextEncoder().encode(secret);
}

export async function signSession(payload: SessionPayload): Promise<string> {
  return new SignJWT({
    name: payload.name,
    email: payload.email,
    role: payload.role,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(payload.sub)
    .setIssuedAt()
    .setExpirationTime(`${SESSION_MAX_AGE_SECONDS}s`)
    .sign(secretKey());
}

/** Returns null for anything invalid, tampered with, or expired. */
export async function verifySession(
  token: string,
): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, secretKey(), {
      algorithms: ["HS256"],
    });

    if (
      typeof payload.sub !== "string" ||
      typeof payload.name !== "string" ||
      typeof payload.email !== "string" ||
      !isRole(payload.role)
    ) {
      return null;
    }

    return {
      sub: payload.sub,
      name: payload.name,
      email: payload.email,
      role: payload.role,
    };
  } catch {
    return null;
  }
}
