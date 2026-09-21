"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/format";

import { useQueryState } from "./useQueryState";

const SORTS = [
  { key: "popular", label: "sortPopular" },
  { key: "price_asc", label: "sortPriceAsc" },
  { key: "price_desc", label: "sortPriceDesc" },
  { key: "new", label: "sortNew" },
] as const;

export function SortSelect() {
  const t = useTranslations("catalog");
  const { params, update, pending } = useQueryState();
  const current = params.get("sort") ?? "popular";
  return (
    <div className={cn("flex items-center gap-1 overflow-x-auto rounded-[13px] bg-platinum-100 p-1 scrollbar-none", pending && "opacity-70")}>
      {SORTS.map((s) => (
        <button
          key={s.key}
          type="button"
          onClick={() => update({ sort: s.key === "popular" ? null : s.key })}
          className={cn(
            "h-8 shrink-0 rounded-[10px] px-3 text-[13px] font-semibold transition",
            current === s.key ? "bg-white text-ink shadow-soft" : "text-platinum-600 hover:text-ink",
          )}
        >
          {t(s.label)}
        </button>
      ))}
    </div>
  );
}
