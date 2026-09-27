"use client";

import { ArrowRight } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Link } from "@/i18n/navigation";
import { cn, formatCount } from "@/lib/format";
import type { CategoryNode } from "@/lib/types";

export function MegaMenu({ categories, onNavigate }: { categories: CategoryNode[]; onNavigate: () => void }) {
  const t = useTranslations();
  const [active, setActive] = useState(categories[0]?.id);
  const reduceMotion = useReducedMotion();
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
                  "relative isolate flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-semibold transition-colors duration-200",
                  cat.id === current.id ? "text-ink" : "text-platinum-700 hover:bg-white/60 hover:text-ink",
                )}
              >
                {cat.id === current.id && (
                  <motion.span
                    layoutId="mega-menu-active-category"
                    className="absolute inset-0 z-0 rounded-xl bg-white shadow-soft"
                    transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 480, damping: 38 }}
                    aria-hidden="true"
                  />
                )}
                <span
                  className={cn(
                    "relative z-10 grid size-9 place-items-center rounded-[10px] transition-colors duration-200",
                    cat.id === current.id ? "bg-ink text-gold-300" : "bg-white text-gold-700 ring-hairline",
                  )}
                >
                  <CategoryIcon name={cat.icon} className="size-5" />
                </span>
                <span className="relative z-10 flex-1">{cat.name}</span>
                <span className="relative z-10 text-[11px] font-medium text-platinum-400">{formatCount(cat.product_count)}</span>
              </Link>
            </li>
          ))}
        </ul>
        <div className="p-6">
          <AnimatePresence initial={false} mode="wait">
            <motion.div
              key={current.id}
              initial={reduceMotion ? { opacity: 1 } : { opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={reduceMotion ? { opacity: 1 } : { opacity: 0, x: -6 }}
              transition={reduceMotion ? { duration: 0 } : { duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="mb-4 flex items-baseline justify-between">
                <h3 className="font-display text-lg font-medium">{current.name}</h3>
                <Link
                  href={`/category/${current.slug}`}
                  onClick={onNavigate}
                  className="group inline-flex items-center gap-1 text-[13px] font-semibold text-gold-700 hover:text-gold-800"
                >
                  {t("common.showAll")} <ArrowRight className="size-3.5 transition-transform duration-200 group-hover:translate-x-1 motion-reduce:transition-none" />
                </Link>
              </div>
              <div className="grid grid-cols-2 gap-2 xl:grid-cols-3">
                {current.children.map((child) => (
                  <Link
                    key={child.id}
                    href={`/category/${child.slug}`}
                    onClick={onNavigate}
                    className="group flex items-center gap-3 rounded-xl p-3 ring-1 ring-transparent transition-[transform,background-color,box-shadow] duration-200 ease-out hover:translate-x-1 hover:bg-platinum-50 hover:ring-platinum-200 motion-reduce:transform-none motion-reduce:transition-none"
                  >
                    <CategoryIcon name={child.icon} className="size-6 text-platinum-400 transition-[color,transform] duration-200 group-hover:scale-105 group-hover:text-gold-600 motion-reduce:transform-none motion-reduce:transition-none" />
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
                    className="rounded-xl p-3 text-[14px] font-medium ring-1 ring-platinum-200 transition-colors duration-200 hover:bg-platinum-50 motion-reduce:transition-none"
                  >
                    {current.name} · {t("common.items", { count: current.product_count })}
                  </Link>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
