import { ChevronLeft, ChevronRight } from "lucide-react";

import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/format";

function pages(current: number, total: number): (number | "…")[] {
  const set = new Set([1, total, current - 1, current, current + 1].filter((p) => p >= 1 && p <= total));
  const sorted = [...set].sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  sorted.forEach((p, i) => {
    if (i && p - sorted[i - 1] > 1) out.push("…");
    out.push(p);
  });
  return out;
}

/** Real links (crawlable) that keep every other query parameter. */
export function Pagination({
  page,
  total,
  path,
  searchParams,
}: {
  page: number;
  total: number;
  path: string;
  searchParams: Record<string, string | undefined>;
}) {
  if (total <= 1) return null;
  const href = (p: number) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(searchParams)) if (v && k !== "page") q.set(k, v);
    if (p > 1) q.set("page", String(p));
    const s = q.toString();
    return `${path}${s ? `?${s}` : ""}`;
  };
  const cell = "grid h-10 min-w-10 place-items-center rounded-[11px] px-3 text-[14px] font-semibold transition";
  return (
    <nav className="mt-10 flex items-center justify-center gap-1.5" aria-label="Сторінки">
      {page > 1 && (
        <Link href={href(page - 1)} className={cn(cell, "ring-1 ring-platinum-200 hover:ring-gold-400")} aria-label="Попередня">
          <ChevronLeft className="size-4" />
        </Link>
      )}
      {pages(page, total).map((p, i) =>
        p === "…" ? (
          <span key={`e${i}`} className="px-1 text-platinum-400">
            …
          </span>
        ) : (
          <Link
            key={p}
            href={href(p)}
            aria-current={p === page ? "page" : undefined}
            className={cn(cell, p === page ? "bg-ink text-white" : "ring-1 ring-platinum-200 hover:ring-gold-400")}
          >
            {p}
          </Link>
        ),
      )}
      {page < total && (
        <Link href={href(page + 1)} className={cn(cell, "ring-1 ring-platinum-200 hover:ring-gold-400")} aria-label="Наступна">
          <ChevronRight className="size-4" />
        </Link>
      )}
    </nav>
  );
}
