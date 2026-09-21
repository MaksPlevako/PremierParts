"use client";

import { Minus, PackageOpen, Plus, Trash2 } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Link } from "@/i18n/navigation";
import { browserApi } from "@/lib/browser-api";
import { cn, finalPrice, formatPrice } from "@/lib/format";
import { cartTotals, useCart } from "@/stores/cart";
import { useHydrated } from "@/lib/use-hydrated";
import { useMyCar } from "@/stores/my-car";

export function CartView() {
  const t = useTranslations();
  const { lines, setQty, remove, replaceProducts } = useCart();
  const car = useMyCar((s) => s.car);
  const mounted = useHydrated();
  const [unavailable, setUnavailable] = useState<number[]>([]);
  const [changed, setChanged] = useState(false);

  // Refresh prices and availability from the server whenever the cart page opens
  useEffect(() => {
    if (!mounted || !lines.length) return;
    browserApi
      .validateCart(lines.map((l) => ({ product_id: l.product.id, qty: l.qty })))
      .then((res) => {
        const fresh = res.items.filter((i) => i.card).map((i) => i.card!);
        const before = new Map(lines.map((l) => [l.product.id, finalPrice(l.product)]));
        setChanged(fresh.some((c) => before.get(c.id) !== finalPrice(c)));
        replaceProducts(fresh);
        setUnavailable(res.items.filter((i) => !i.available).map((i) => i.product_id));
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  if (!mounted) return <div className="h-64 animate-pulse rounded-[24px] bg-platinum-50" />;

  if (!lines.length) {
    return (
      <div className="flex flex-col items-center gap-4 rounded-[26px] bg-platinum-50 px-6 py-20 text-center ring-1 ring-platinum-200">
        <PackageOpen className="size-12 text-gold-600" />
        <p className="font-display text-[22px] font-medium">{t("cart.empty")}</p>
        <p className="text-[14px] text-platinum-600">{t("cart.emptyHint")}</p>
        <Link href="/catalog" className="mt-2 inline-flex h-12 items-center rounded-[14px] bg-ink px-6 font-semibold text-white">
          {t("cart.toCatalog")}
        </Link>
      </div>
    );
  }

  const available = lines.filter((l) => !unavailable.includes(l.product.id));
  const totals = cartTotals(available);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
      <div className="flex flex-col gap-3">
        {changed && <p className="rounded-[12px] bg-gold-50 px-4 py-2.5 text-[13px] font-medium text-warning ring-1 ring-gold-200">{t("cart.priceChanged")}</p>}
        <AnimatePresence initial={false}>
          {lines.map(({ product, qty }) => {
            const gone = unavailable.includes(product.id);
            const price = finalPrice(product);
            return (
              <motion.div
                key={product.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20, height: 0, marginBottom: 0 }}
                className={cn("flex gap-4 rounded-[20px] bg-white p-3 ring-1 ring-platinum-200 sm:p-4", gone && "opacity-60")}
              >
                <Link href={`/product/${product.slug}`} className="relative size-24 shrink-0 overflow-hidden rounded-[14px] bg-platinum-100 sm:h-24 sm:w-32">
                  {product.image && <Image src={product.image} alt="" fill sizes="128px" className="object-cover" />}
                </Link>
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <Link href={`/product/${product.slug}`} className="line-clamp-2 text-[14px] font-semibold hover:text-gold-800">
                    {product.name}
                  </Link>
                  <p className="text-[12px] text-platinum-500">{[product.manufacturer, product.sku].filter(Boolean).join(" · ")}</p>
                  {gone && <p className="text-[12px] font-semibold text-danger">{t("cart.unavailable")}</p>}
                  <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-2">
                    <div className="flex h-10 items-center rounded-[12px] ring-1 ring-platinum-200">
                      <button type="button" onClick={() => setQty(product.id, qty - 1)} className="grid size-10 place-items-center" aria-label="Менше">
                        <Minus className="size-3.5" />
                      </button>
                      <span className="w-7 text-center text-[14px] font-semibold">{qty}</span>
                      <button type="button" onClick={() => setQty(product.id, qty + 1)} className="grid size-10 place-items-center" aria-label="Більше">
                        <Plus className="size-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-display text-[17px] font-medium">{formatPrice(price * qty, t("common.priceOnRequest"))}</span>
                      <button
                        type="button"
                        onClick={() => remove(product.id)}
                        className="grid size-9 place-items-center rounded-[10px] text-platinum-400 hover:bg-platinum-50 hover:text-danger"
                        aria-label={t("cart.remove")}
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      <aside className="h-fit rounded-[24px] bg-white p-6 ring-1 ring-platinum-200 lg:sticky lg:top-[92px]">
        <p className="font-display text-[18px] font-medium">{t("checkout.summary")}</p>
        <dl className="mt-5 flex flex-col gap-2 text-[14px]">
          <div className="flex justify-between">
            <dt className="text-platinum-600">{t("cart.subtotal")}</dt>
            <dd className="font-semibold">{formatPrice(totals.subtotal, "—")}</dd>
          </div>
          {totals.discount > 0 && (
            <div className="flex justify-between text-success">
              <dt>{t("cart.discount")}</dt>
              <dd className="font-semibold">−{formatPrice(totals.discount)}</dd>
            </div>
          )}
          <div className="mt-2 flex items-baseline justify-between border-t border-platinum-100 pt-4">
            <dt className="font-semibold">{t("cart.total")}</dt>
            <dd className="font-display text-[26px] font-medium">{formatPrice(totals.total, "—")}</dd>
          </div>
        </dl>
        {totals.unpriced > 0 && <p className="mt-3 text-[12.5px] text-platinum-500">{t("cart.priceOnRequestNote")}</p>}
        {car && <p className="mt-3 rounded-[12px] bg-platinum-50 px-3 py-2 text-[12.5px] text-platinum-600">{t("checkout.car")}: <b className="text-ink">{car.full_label}</b></p>}
        <Link
          href="/checkout"
          className={cn(
            "mt-5 flex h-13 items-center justify-center rounded-[14px] bg-gold font-bold text-[#1e1606] shadow-gold",
            !available.length && "pointer-events-none opacity-50",
          )}
        >
          {t("cart.checkout")}
        </Link>
        <Link href="/catalog" className="mt-3 block text-center text-[13px] font-semibold text-platinum-600 hover:text-ink">
          {t("cart.continue")}
        </Link>
      </aside>
    </div>
  );
}
