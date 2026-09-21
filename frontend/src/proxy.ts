import createMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";

import { routing } from "./i18n/routing";

const intl = createMiddleware(routing);
const backend = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
const LEGACY = /^\/(mark|model)\//;

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  // Old site URLs (/mark/544, /model/544/25775/24560) keep their SEO weight via 301s
  if (LEGACY.test(pathname)) {
    try {
      const res = await fetch(`${backend}/api/legacy/resolve?path=${encodeURIComponent(pathname)}`, {
        cache: "no-store",
      });
      if (res.ok) {
        const { location } = (await res.json()) as { location: string };
        return NextResponse.redirect(new URL(location, request.url), 301);
      }
    } catch {
      // fall through to a normal 404
    }
  }
  return intl(request);
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|media|static|admin|brand|.*\\..*).*)"],
};
