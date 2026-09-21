"use client";

import { ShoppingBag } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import { cartCount, useCart } from "@/stores/cart";
import { useHydrated } from "@/lib/use-hydrated";

export function CartButton() {
  const t = useTranslations("header");
  const lines = useCart((s) => s.lines);
  const mounted = useHydrated();
  const count = mounted ? cartCount(lines) : 0;

  return (
    <Link
      href="/cart"
      id="cart-button"
      aria-label={t("cart")}
      className="relative grid size-11 place-items-center rounded-[14px] bg-gold text-[#1e1606] shadow-gold transition-transform active:scale-95"
    >
      <ShoppingBag className="size-5" />
      <AnimatePresence>
        {count > 0 && (
          <motion.span
            key={count}
            initial={{ scale: 0.4, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.4, opacity: 0 }}
            transition={{ type: "spring", stiffness: 500, damping: 22 }}
            className="absolute -top-1.5 -right-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-ink px-1 text-[10px] font-bold text-white ring-2 ring-white"
          >
            {count}
          </motion.span>
        )}
      </AnimatePresence>
    </Link>
  );
}
