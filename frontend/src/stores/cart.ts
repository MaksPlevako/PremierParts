"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { finalPrice } from "@/lib/format";
import type { ProductCard } from "@/lib/types";

export interface CartLine {
  product: ProductCard;
  qty: number;
}

interface CartState {
  lines: CartLine[];
  add: (product: ProductCard, qty?: number) => void;
  setQty: (productId: number, qty: number) => void;
  remove: (productId: number) => void;
  replaceProducts: (cards: ProductCard[]) => void;
  clear: () => void;
}

const clampQty = (qty: number) => Math.max(1, Math.min(99, Math.round(qty)));

export const useCart = create<CartState>()(
  persist(
    (set) => ({
      lines: [],
      add: (product, qty = 1) =>
        set((state) => {
          const existing = state.lines.find((l) => l.product.id === product.id);
          if (existing) {
            return {
              lines: state.lines.map((l) =>
                l.product.id === product.id ? { product, qty: clampQty(l.qty + qty) } : l,
              ),
            };
          }
          return { lines: [...state.lines, { product, qty: clampQty(qty) }] };
        }),
      setQty: (productId, qty) =>
        set((state) => ({
          lines: state.lines.map((l) => (l.product.id === productId ? { ...l, qty: clampQty(qty) } : l)),
        })),
      remove: (productId) => set((state) => ({ lines: state.lines.filter((l) => l.product.id !== productId) })),
      replaceProducts: (cards) =>
        set((state) => {
          const byId = new Map(cards.map((c) => [c.id, c]));
          return { lines: state.lines.map((l) => ({ ...l, product: byId.get(l.product.id) ?? l.product })) };
        }),
      clear: () => set({ lines: [] }),
    }),
    { name: "pp-cart", version: 1, storage: createJSONStorage(() => localStorage) },
  ),
);

export function cartCount(lines: CartLine[]): number {
  return lines.reduce((sum, l) => sum + l.qty, 0);
}

export function cartTotals(lines: CartLine[]) {
  let subtotal = 0;
  let total = 0;
  let unpriced = 0;
  for (const { product, qty } of lines) {
    const base = product.sale_price != null && product.old_price ? product.old_price : product.price;
    subtotal += base * qty;
    total += finalPrice(product) * qty;
    if (!product.price) unpriced += qty;
  }
  return { subtotal, total, discount: subtotal - total, unpriced };
}
