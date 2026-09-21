"use client";

import { Minus, Plus, Zap } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { FitBadge } from "@/components/car/FitBadge";
import { Link } from "@/i18n/navigation";
import { cn, formatPrice } from "@/lib/format";
import type { ProductDetail } from "@/lib/types";

import { AddToCartButton } from "./AddToCartButton";
import { QuickOrderDialog } from "./QuickOrderDialog";

export function BuyBox({ product }: { product: ProductDetail }) {
  const t = useTranslations();
  const [qty, setQty] = useState(1);
  const [quickOpen, setQuickOpen] = useState(false);
  const price = product.sale_price ?? product.price;
  const saving = product.old_price && price ? product.old_price - price : 0;

  return (
    <div className="flex flex-col gap-5 rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-[12px] font-bold",
            product.stock_status === "in_stock" ? "bg-success-soft text-success" : "bg-gold-50 text-warning",
          )}
        >
          ● {t(`stock.${product.stock_status}`)}
        </span>
        {product.promotion && (
          <Link
            href={`/promotions/${product.promotion.slug}`}
            className="rounded-full bg-ink px-2.5 py-1 text-[12px] font-bold text-gold-200 hover:bg-graphite-700"
          >
            {t("product.promo", { title: product.promotion.title })}
          </Link>
        )}
      </div>

      <div>
        {product.old_price && price ? (
          <div className="flex items-center gap-2">
            <span className="text-[15px] text-platinum-400 line-through">{formatPrice(product.old_price)}</span>
            {product.discount_percent && (
              <span className="rounded-md bg-gold-100 px-1.5 py-0.5 text-[12px] font-bold text-gold-800">−{product.discount_percent}%</span>
            )}
          </div>
        ) : null}
        <p className={cn("font-display font-medium text-ink", price ? "text-[38px] leading-tight" : "text-[22px]")}>
          {formatPrice(price, t("common.priceOnRequest"))}
        </p>
        {saving > 0 && <p className="mt-1 text-[13px] font-semibold text-success">{t("product.save", { amount: formatPrice(saving) })}</p>}
      </div>

      <FitBadge generationIds={product.generation_ids} size="lg" />

      <div className="flex flex-col gap-3 sm:flex-row">
        {price > 0 && (
          <div className="flex h-12 items-center rounded-[14px] ring-1 ring-platinum-200">
            <button type="button" onClick={() => setQty((q) => Math.max(1, q - 1))} className="grid size-12 place-items-center" aria-label="Менше">
              <Minus className="size-4" />
            </button>
            <span className="w-8 text-center font-semibold">{qty}</span>
            <button type="button" onClick={() => setQty((q) => Math.min(99, q + 1))} className="grid size-12 place-items-center" aria-label="Більше">
              <Plus className="size-4" />
            </button>
          </div>
        )}
        <AddToCartButton product={product} qty={qty} />
      </div>
      {price > 0 && (
        <button
          type="button"
          onClick={() => setQuickOpen(true)}
          className="inline-flex h-12 items-center justify-center gap-2 rounded-[14px] bg-gold font-bold text-[#1e1606] shadow-gold"
        >
          <Zap className="size-4" /> {t("common.buyOneClick")}
        </button>
      )}
      <QuickOrderDialog product={product} open={quickOpen} onClose={() => setQuickOpen(false)} />
    </div>
  );
}
