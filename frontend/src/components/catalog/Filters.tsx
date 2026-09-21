"use client";

import { Check, SlidersHorizontal, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Dialog } from "@/components/ui/Dialog";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/format";
import type { ListingResult } from "@/lib/types";

import { useQueryState } from "./useQueryState";

interface Props {
  facets: ListingResult["facets"];
  priceRange: ListingResult["price_range"];
  count: number;
  /** Where category chips link to (the current listing path with ?category= for search, or /category/<slug>). */
  categoryHref?: (slug: string) => string;
  showCategories?: boolean;
}

function Check2({ checked }: { checked: boolean }) {
  return (
    <span
      className={cn(
        "grid size-[18px] shrink-0 place-items-center rounded-[6px] ring-1 transition",
        checked ? "bg-ink text-gold-300 ring-ink" : "bg-white ring-platinum-300",
      )}
    >
      {checked && <Check className="size-3" strokeWidth={3} />}
    </span>
  );
}

function FilterBody({ facets, priceRange, categoryHref, showCategories = true }: Omit<Props, "count">) {
  const t = useTranslations("catalog");
  const tStock = useTranslations("stock");
  const { params, update } = useQueryState();
  const selectedMakers = (params.get("manufacturer") ?? "").split(",").filter(Boolean);
  const side = params.get("side");
  const stock = params.get("stock");

  const toggleMaker = (id: number) => {
    const set = new Set(selectedMakers);
    if (set.has(String(id))) set.delete(String(id));
    else set.add(String(id));
    update({ manufacturer: [...set].join(",") || null });
  };

  const group = "border-b border-platinum-100 py-5 first:pt-0 last:border-0";
  const title = "mb-3 text-[12px] font-bold tracking-[0.14em] text-platinum-500 uppercase";

  return (
    <div className="flex flex-col">
      {showCategories && facets.categories.length > 0 && categoryHref && (
        <div className={group}>
          <p className={title}>{t("subcategories")}</p>
          <ul className="flex flex-col gap-0.5">
            {facets.categories.map((c) => (
              <li key={c.id}>
                <Link
                  href={categoryHref(c.slug)}
                  className="flex items-center justify-between rounded-[9px] px-2 py-1.5 text-[14px] text-platinum-700 hover:bg-platinum-50 hover:text-ink"
                >
                  <span className="truncate">{c.name}</span>
                  <span className="text-[12px] text-platinum-400">{c.count}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {facets.manufacturers.length > 0 && (
        <div className={group}>
          <p className={title}>{t("manufacturer")}</p>
          <ul className="flex max-h-64 flex-col gap-0.5 overflow-y-auto pr-1">
            {facets.manufacturers.map((m) => {
              const checked = selectedMakers.includes(String(m.id));
              return (
                <li key={m.id}>
                  <button
                    type="button"
                    onClick={() => toggleMaker(m.id)}
                    className="flex w-full items-center gap-2.5 rounded-[9px] px-2 py-1.5 text-left text-[14px] hover:bg-platinum-50"
                  >
                    <Check2 checked={checked} />
                    <span className={cn("flex-1 truncate", checked && "font-semibold text-ink")}>{m.name}</span>
                    <span className="text-[12px] text-platinum-400">{m.count}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {(facets.side.left > 0 || facets.side.right > 0) && (
        <div className={group}>
          <p className={title}>{t("side")}</p>
          <div className="grid grid-cols-2 gap-2">
            {(["left", "right"] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => update({ side: side === s ? null : s })}
                className={cn(
                  "h-10 rounded-[11px] text-[13px] font-semibold ring-1 transition",
                  side === s ? "bg-ink text-white ring-ink" : "ring-platinum-200 hover:ring-gold-400",
                )}
              >
                {t(s)} <span className="font-normal opacity-60">{facets.side[s]}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={group}>
        <p className={title}>{t("availability")}</p>
        <div className="flex flex-col gap-0.5">
          {(["in_stock", "on_order"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => update({ stock: stock === s ? null : s })}
              className="flex w-full items-center gap-2.5 rounded-[9px] px-2 py-1.5 text-left text-[14px] hover:bg-platinum-50"
            >
              <Check2 checked={stock === s} />
              <span className="flex-1">{tStock(s)}</span>
              <span className="text-[12px] text-platinum-400">{facets.stock[s]}</span>
            </button>
          ))}
        </div>
      </div>

      {priceRange.max > 0 && (
        <div className={group}>
          <p className={title}>{t("price")}</p>
          <PriceRange
            key={`${params.get("price_min") ?? ""}-${params.get("price_max") ?? ""}`}
            min={params.get("price_min") ?? ""}
            max={params.get("price_max") ?? ""}
            range={priceRange}
            onApply={(min, max) => update({ price_min: min || null, price_max: max || null })}
          />
        </div>
      )}
    </div>
  );
}

function PriceRange({
  min,
  max,
  range,
  onApply,
}: {
  min: string;
  max: string;
  range: ListingResult["price_range"];
  onApply: (min: string, max: string) => void;
}) {
  const t = useTranslations("catalog");
  const [priceMin, setPriceMin] = useState(min);
  const [priceMax, setPriceMax] = useState(max);
  const input =
    "h-10 w-full min-w-0 rounded-[10px] px-3 text-[13px] ring-1 ring-platinum-200 outline-none focus:ring-2 focus:ring-gold-400";
  return (
    <form
      className="flex items-center gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        onApply(priceMin, priceMax);
      }}
    >
      <input
        inputMode="numeric"
        value={priceMin}
        onChange={(e) => setPriceMin(e.target.value.replace(/\D/g, ""))}
        placeholder={`${t("priceFrom")} ${Math.floor(range.min)}`}
        className={input}
      />
      <span className="text-platinum-400">—</span>
      <input
        inputMode="numeric"
        value={priceMax}
        onChange={(e) => setPriceMax(e.target.value.replace(/\D/g, ""))}
        placeholder={`${t("priceTo")} ${Math.ceil(range.max)}`}
        className={input}
      />
      <button type="submit" className="h-10 shrink-0 rounded-[10px] bg-ink px-3 text-[13px] font-semibold text-white">
        OK
      </button>
    </form>
  );
}

export function Filters(props: Props) {
  const t = useTranslations("catalog");
  const { params, update, pending } = useQueryState();
  const [open, setOpen] = useState(false);
  const active = ["manufacturer", "side", "stock", "price_min", "price_max"].filter((k) => params.get(k)).length;

  const reset = () => update({ manufacturer: null, side: null, stock: null, price_min: null, price_max: null });

  return (
    <>
      <aside className={cn("hidden transition-opacity lg:block", pending && "opacity-60")}>
        <div className="sticky top-[88px] rounded-[20px] bg-white p-5 ring-1 ring-platinum-200">
          <div className="mb-4 flex items-center justify-between">
            <p className="font-display text-[15px] font-medium">{t("filters")}</p>
            {active > 0 && (
              <button type="button" onClick={reset} className="inline-flex items-center gap-1 text-[12px] font-semibold text-gold-700">
                <X className="size-3.5" /> {t("resetFilters")}
              </button>
            )}
          </div>
          <FilterBody {...props} />
        </div>
      </aside>
      <div className="lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="inline-flex h-10 items-center gap-2 rounded-[12px] px-4 text-[13px] font-semibold ring-1 ring-platinum-200"
        >
          <SlidersHorizontal className="size-4" /> {t("filters")}
          {active > 0 && <span className="grid size-5 place-items-center rounded-full bg-ink text-[10px] text-white">{active}</span>}
        </button>
        <Dialog open={open} onClose={() => setOpen(false)} title={t("filters")}>
          <div className="p-5">
            <FilterBody {...props} />
          </div>
          <div className="sticky bottom-0 flex gap-2 border-t border-platinum-100 bg-white p-4">
            <button type="button" onClick={reset} className="h-12 flex-1 rounded-[14px] font-semibold ring-1 ring-platinum-200">
              {t("resetFilters")}
            </button>
            <button type="button" onClick={() => setOpen(false)} className="h-12 flex-1 rounded-[14px] bg-ink font-semibold text-white">
              {t("applyFilters", { count: props.count })}
            </button>
          </div>
        </Dialog>
      </div>
    </>
  );
}
