"use client";

import { ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Link } from "@/i18n/navigation";
import { cn, formatCount } from "@/lib/format";
import type { CategoryNode } from "@/lib/types";

export function MegaMenu({ categories, onNavigate }: { categories: CategoryNode[]; onNavigate: () => void }) {
  const t = useTranslations();
  const [active, setActive] = useState(categories[0]?.id);
  const current = categories.find((c) => c.id === active) ?? categories[0];
  if (!current) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className="absolute inset-x-0 top-[68px] z-40 px-6 pt-2"
    >
      <div className="mx-auto grid max-w-[1320px] grid-cols-[300px_1fr] overflow-hidden rounded-[22px] bg-white shadow-float">
        <ul className="border-r border-platinum-100 bg-platinum-50 p-3">
          {categories.map((cat) => (
            <li key={cat.id}>
              <Link
                href={`/category/${cat.slug}`}
                onMouseEnter={() => setActive(cat.id)}
                onFocus={() => setActive(cat.id)}
                onClick={onNavigate}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-semibold transition-colors",
                  cat.id === current.id ? "bg-white text-ink shadow-soft" : "text-platinum-700 hover:text-ink",
                )}
              >
                <span
                  className={cn(
                    "grid size-9 place-items-center rounded-[10px] transition-colors",
                    cat.id === current.id ? "bg-ink text-gold-300" : "bg-white text-gold-700 ring-hairline",
                  )}
                >
                  <CategoryIcon name={cat.icon} className="size-5" />
                </span>
                <span className="flex-1">{cat.name}</span>
                <span className="text-[11px] font-medium text-platinum-400">{formatCount(cat.product_count)}</span>
              </Link>
            </li>
          ))}
        </ul>
        <div className="p-6">
          <div className="mb-4 flex items-baseline justify-between">
            <h3 className="font-display text-lg font-medium">{current.name}</h3>
            <Link
              href={`/category/${current.slug}`}
              onClick={onNavigate}
              className="inline-flex items-center gap-1 text-[13px] font-semibold text-gold-700 hover:text-gold-800"
            >
              {t("common.showAll")} <ArrowRight className="size-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-2 xl:grid-cols-3">
            {current.children.map((child) => (
              <Link
                key={child.id}
                href={`/category/${child.slug}`}
                onClick={onNavigate}
                className="group flex items-center gap-3 rounded-xl p-3 ring-1 ring-transparent transition hover:bg-platinum-50 hover:ring-platinum-200"
              >
                <CategoryIcon name={child.icon} className="size-6 text-platinum-400 transition-colors group-hover:text-gold-600" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[14px] font-medium text-ink">{child.name}</span>
                  <span className="text-[12px] text-platinum-500">{t("common.items", { count: child.product_count })}</span>
                </span>
              </Link>
            ))}
            {current.children.length === 0 && (
              <Link
                href={`/category/${current.slug}`}
                onClick={onNavigate}
                className="rounded-xl p-3 text-[14px] font-medium ring-1 ring-platinum-200 hover:bg-platinum-50"
              >
                {current.name} · {t("common.items", { count: current.product_count })}
              </Link>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
