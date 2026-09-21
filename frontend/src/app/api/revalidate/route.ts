import { revalidateTag } from "next/cache";
import type { NextRequest } from "next/server";

/** Called by Django signals after admin edits: {"tags": ["product:slug", "home", ...]}. */
export async function POST(request: NextRequest) {
  const secret = process.env.REVALIDATE_SECRET ?? "dev-revalidate-secret";
  if (request.headers.get("x-revalidate-secret") !== secret) {
    return Response.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
  const body = (await request.json().catch(() => ({}))) as { tags?: unknown };
  const tags = Array.isArray(body.tags) ? body.tags.filter((t): t is string => typeof t === "string").slice(0, 50) : [];
  // Admin edits must be visible on the very next page view, so expire immediately instead of stale-while-revalidate.
  for (const tag of tags) revalidateTag(tag, { expire: 0 });
  return Response.json({ ok: true, revalidated: tags, now: Date.now() });
}
