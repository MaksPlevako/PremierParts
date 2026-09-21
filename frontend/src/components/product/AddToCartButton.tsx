"use client";

import { Check, MessageCircleQuestion, ShoppingBag } from "lucide-react";
import { animate } from "motion";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";

import { toast } from "@/components/ui/Toaster";
import { cn } from "@/lib/format";
import type { ProductCard } from "@/lib/types";
import { useCart } from "@/stores/cart";

import { QuickOrderDialog } from "./QuickOrderDialog";

/** Flies a small gold dot from the button into the cart icon in the header. */
function flyToCart(from: HTMLElement) {
  const target = document.getElementById("cart-button");
  if (!target || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const a = from.getBoundingClientRect();
  const b = target.getBoundingClientRect();
  const dot = document.createElement("span");
  dot.className = "pointer-events-none fixed z-[100] size-4 rounded-full bg-gold shadow-gold";
  dot.style.left = `${a.left + a.width / 2 - 8}px`;
  dot.style.top = `${a.top + a.height / 2 - 8}px`;
  document.body.appendChild(dot);
  const dx = b.left + b.width / 2 - (a.left + a.width / 2);
  const dy = b.top + b.height / 2 - (a.top + a.height / 2);
  animate(
    dot,
    { transform: ["translate(0,0) scale(1)", `translate(${dx * 0.5}px, ${dy - 80}px) scale(1.3)`, `translate(${dx}px, ${dy}px) scale(.4)`] },
    { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  ).then(() => {
    dot.remove();
    animate(target, { scale: [1, 1.18, 1] }, { duration: 0.35 });
  });
}

export function AddToCartButton({ product, compact = false, qty = 1 }: { product: ProductCard; compact?: boolean; qty?: number }) {
  const t = useTranslations();
  const add = useCart((s) => s.add);
  const inCart = useCart((s) => s.lines.some((l) => l.product.id === product.id));
  const ref = useRef<HTMLButtonElement>(null);
  const [askOpen, setAskOpen] = useState(false);
  const noPrice = !product.price;

  if (noPrice) {
    return (
      <>
        <button
          type="button"
          onClick={() => setAskOpen(true)}
          className={cn(
            "inline-flex shrink-0 items-center justify-center gap-1.5 font-semibold ring-1 ring-platinum-200 transition hover:ring-gold-400",
            compact ? "h-9 rounded-[10px] px-2.5 text-[12px]" : "h-12 rounded-[14px] px-5 text-[14px]",
          )}
        >
          <MessageCircleQuestion className="size-4 text-gold-700" />
          {compact ? t("common.askPrice").split(" ")[0] : t("common.askPrice")}
        </button>
        <QuickOrderDialog product={product} open={askOpen} onClose={() => setAskOpen(false)} mode="ask" />
      </>
    );
  }

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => {
        add(product, qty);
        if (ref.current) flyToCart(ref.current);
        toast({ title: t("cart.added"), text: product.name, image: product.image });
      }}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-2 font-semibold transition-colors active:scale-95",
        compact ? "h-9 rounded-[10px] px-3 text-[12px]" : "h-12 flex-1 rounded-[14px] px-6 text-[15px]",
        inCart ? "bg-success-soft text-success" : "bg-ink text-white hover:bg-graphite-700",
      )}
      aria-label={t("common.addToCart")}
    >
      {inCart ? <Check className="size-4" /> : <ShoppingBag className="size-4" />}
      <span className={cn(compact && "hidden sm:inline")}>{inCart ? t("common.inCart") : t("common.addToCart")}</span>
    </button>
  );
}
