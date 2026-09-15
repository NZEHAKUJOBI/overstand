import bcrypt from "bcryptjs";
import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";
import { Types } from "mongoose";
import { can, type Permission } from "./rbac";
import {
  SESSION_COOKIE,
  SESSION_MAX_AGE_SECONDS,
  signSession,
  verifySession,
  type SessionPayload,
} from "./session";

/** Node-runtime auth: cookies, password hashing, and route guards. */

const BCRYPT_ROUNDS = 12;

export async function hashPassword(plain: string): Promise<string> {
  return bcrypt.hash(plain, BCRYPT_ROUNDS);
}

export async function verifyPassword(
  plain: string,
  hash: string,
): Promise<boolean> {
  return bcrypt.compare(plain, hash);
}

/**
 * Whether to mark the session cookie Secure.
 *
 * Keyed off the request protocol rather than NODE_ENV: a production build run
 * locally over plain HTTP would otherwise set a Secure cookie that the browser
 * refuses to store, producing a silent login loop. Render terminates TLS at
 * its proxy and forwards `x-forwarded-proto`, so real deployments still get
 * Secure. Falls back to NODE_ENV when the header is absent.
 */
async function secureCookieEnabled(): Promise<boolean> {
  const proto = (await headers()).get("x-forwarded-proto");
  if (proto) return proto.split(",")[0].trim() === "https";
  return process.env.NODE_ENV === "production";
}

export async function startSession(payload: SessionPayload): Promise<void> {
  const token = await signSession(payload);
  const jar = await cookies();

  jar.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: await secureCookieEnabled(),
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
}

export async function endSession(): Promise<void> {
  const jar = await cookies();
  jar.delete(SESSION_COOKIE);
}

export async function getSession(): Promise<SessionPayload | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  return token ? verifySession(token) : null;
}

/**
 * Guards a page or server action. `middleware.ts` already redirects
 * unauthenticated traffic away from /admin, but that is a convenience layer —
 * this is the check that actually protects the data, and server actions are
 * reachable without ever passing through a matched route.
 */
export async function requireSession(): Promise<SessionPayload> {
  const session = await getSession();
  if (!session) redirect("/login");
  return session;
}

export async function requirePermission(
  permission: Permission,
): Promise<SessionPayload> {
  const session = await requireSession();

  if (!can(session.role, permission)) {
    redirect(`/admin/no-access?need=${encodeURIComponent(permission)}`);
  }

  return session;
}

/**
 * For server actions, which should return an error to the form rather than
 * redirect the user away mid-submission.
 */
export async function checkPermission(
  permission: Permission,
): Promise<{ session: SessionPayload } | { error: string }> {
  const session = await getSession();
  if (!session) return { error: "Your session has expired. Sign in again." };

  if (!can(session.role, permission)) {
    return { error: "Your role does not permit this action." };
  }

  return { session };
}

/** The acting admin's id, for stamping `createdBy` / `recordedBy`. */
export function actorId(session: SessionPayload): Types.ObjectId {
  return new Types.ObjectId(session.sub);
}
