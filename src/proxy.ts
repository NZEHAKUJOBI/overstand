import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/session";

/**
 * Keeps signed-out traffic off /admin and signed-in traffic off /login.
 * (Next 16 renamed the `middleware` convention to `proxy`.)
 *
 * This is a convenience layer, not the security boundary — server actions are
 * reachable without matching a route here. Every page and action calls
 * `requireSession` / `checkPermission` for the check that actually counts.
 */
export default async function proxy(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const session = token ? await verifySession(token) : null;
  const { pathname, search } = request.nextUrl;

  if (pathname.startsWith("/admin") && !session) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = "";
    url.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(url);
  }

  if (pathname === "/login" && session) {
    const url = request.nextUrl.clone();
    url.pathname = "/admin";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/login"],
};
